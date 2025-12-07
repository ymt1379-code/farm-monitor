import streamlit as st
import json
import os
import folium
from streamlit_folium import st_folium
import pandas as pd

DATA_FILE = "farms.json"

# -----------------------------
# データ読み書き
# -----------------------------
def load_data():
    # farms.json が無い or 壊れている場合もここで初期化
    if not os.path.exists(DATA_FILE):
        data = {"jas": []}
        save_data(data)
        return data
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # 想定外構造だった場合も初期化
        if "jas" not in data:
            data = {"jas": []}
            save_data(data)
        return data
    except Exception:
        data = {"jas": []}
        save_data(data)
        return data


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


data = load_data()

# -----------------------------
# 共通ヘッダ
# -----------------------------
st.title("農地管理クラウドシステム（β）")
st.sidebar.title("農地管理メニュー")

menu = st.sidebar.selectbox(
    "メニューを選択してください",
    [
        "地図表示",
        "農協登録",
        "農家登録",
        "農地登録",
        "農協編集",
        "農家編集",
        "農地編集",
        "農地ナビ取込",
    ],
)

# -----------------------------
# 地図表示（有効な農地のみ）
# -----------------------------
if menu == "地図表示":
    center = [34.230532, 135.170785]  # 和歌山市役所
    m = folium.Map(location=center, zoom_start=13, tiles="OpenStreetMap")

    for ja in data["jas"]:
        for farmer in ja["farmers"]:
            for land in farmer["lands"]:
                if land.get("is_active", True):
                    tooltip = f"{ja['ja_name']} / {farmer['farmer_name']} / {land['land_name']}"
                    folium.Marker(
                        [land["lat"], land["lon"]],
                        tooltip=tooltip,
                    ).add_to(m)

    st_folium(m, width=900, height=600)

# -----------------------------
# 農協登録
# -----------------------------
elif menu == "農協登録":
    st.subheader("農協登録")

    ja_name = st.text_input("農協名（例：わかやま）")

    if st.button("農協を登録"):
        if not ja_name:
            st.error("農協名を入力してください")
        else:
            ja_id = f"JA-{len(data['jas']) + 1:03}"
            data["jas"].append(
                {"ja_id": ja_id, "ja_name": ja_name, "farmers": []}
            )
            save_data(data)
            st.success(f"農協「{ja_name}」を登録しました（ID: {ja_id}）")

# -----------------------------
# 農家登録
# -----------------------------
elif menu == "農家登録":
    st.subheader("農家登録")

    if not data["jas"]:
        st.warning("先に『農協登録』から農協を登録してください。")
    else:
        ja_name = st.selectbox("農協を選択", [j["ja_name"] for j in data["jas"]])
        farmer_name = st.text_input("農家名（例：岡農園）")

        if st.button("農家を登録"):
            if not farmer_name:
                st.error("農家名を入力してください")
            else:
                ja_obj = next(j for j in data["jas"] if j["ja_name"] == ja_name)
                farmer_id = f"FARM-{len(ja_obj['farmers']) + 1:03}"
                ja_obj["farmers"].append(
                    {
                        "farmer_id": farmer_id,
                        "farmer_name": farmer_name,
                        "lands": [],
                    }
                )
                save_data(data)
                st.success(
                    f"農協「{ja_name}」に農家「{farmer_name}」を登録しました（ID: {farmer_id}）"
                )

# -----------------------------
# 農地登録
# -----------------------------
elif menu == "農地登録":
    st.subheader("農地登録")

    if not data["jas"]:
        st.warning("農協が登録されていません。まず『農協登録』してください。")
    else:
        ja_name = st.selectbox("農協", [j["ja_name"] for j in data["jas"]])
        ja_obj = next(j for j in data["jas"] if j["ja_name"] == ja_name)

        if not ja_obj["farmers"]:
            st.warning("この農協にはまだ農家が登録されていません。『農家登録』してください。")
        else:
            farmer_name = st.selectbox(
                "農家", [f["farmer_name"] for f in ja_obj["farmers"]]
            )
            farmer_obj = next(
                f for f in ja_obj["farmers"] if f["farmer_name"] == farmer_name
            )

            land_name = st.text_input("農地名（例：本宅前の田）")
            address = st.text_input("住所（メモ用でも可）")
            lat = st.number_input("緯度", format="%.8f")
            lon = st.number_input("経度", format="%.8f")

            if st.button("農地を登録"):
                if not land_name:
                    st.error("農地名を入力してください")
                else:
                    land_id = f"LAND-{len(farmer_obj['lands']) + 1:03}"
                    farmer_obj["lands"].append(
                        {
                            "land_id": land_id,
                            "land_name": land_name,
                            "address": address,
                            "lat": float(lat),
                            "lon": float(lon),
                            "is_active": True,
                        }
                    )
                    save_data(data)
                    st.success(
                        f"農地「{land_name}」を登録しました（ID: {land_id}／初期状態: 有効）"
                    )

# -----------------------------
# 農協編集（名称変更・削除）
# -----------------------------
elif menu == "農協編集":
    st.subheader("農協編集")

    if not data["jas"]:
        st.warning("農協データがありません。")
    else:
        ja_names = [j["ja_name"] for j in data["jas"]]
        ja_name = st.selectbox("編集する農協を選択", ja_names)
        ja_obj = next(j for j in data["jas"] if j["ja_name"] == ja_name)

        new_name = st.text_input("農協名（編集）", value=ja_obj["ja_name"])
        delete_flag = st.checkbox("この農協を削除する（所属農家・農地も全て削除）")
        confirm_delete = False
        if delete_flag:
            confirm_delete = st.checkbox("本当に削除してよい場合はチェック")

        if st.button("変更を保存"):
            if delete_flag and confirm_delete:
                data["jas"] = [j for j in data["jas"] if j["ja_id"] != ja_obj["ja_id"]]
                save_data(data)
                st.success(f"農協「{ja_name}」を削除しました。")
            else:
                ja_obj["ja_name"] = new_name
                save_data(data)
                st.success("農協名を更新しました。")

# -----------------------------
# 農家編集（名称変更・削除）
# -----------------------------
elif menu == "農家編集":
    st.subheader("農家編集")

    if not data["jas"]:
        st.warning("農協がありません。")
    else:
        ja_names = [j["ja_name"] for j in data["jas"]]
        ja_name = st.selectbox("農協を選択", ja_names)
        ja_obj = next(j for j in data["jas"] if j["ja_name"] == ja_name)

        if not ja_obj["farmers"]:
            st.warning("この農協には農家がありません。")
        else:
            farmer_names = [f["farmer_name"] for f in ja_obj["farmers"]]
            farmer_name = st.selectbox("編集する農家を選択", farmer_names)
            farmer_obj = next(
                f for f in ja_obj["farmers"] if f["farmer_name"] == farmer_name
            )

            new_name = st.text_input("農家名（編集）", value=farmer_obj["farmer_name"])
            delete_flag = st.checkbox(
                "この農家を削除する（所属農地も全て削除）"
            )
            confirm_delete = False
            if delete_flag:
                confirm_delete = st.checkbox("本当に削除してよい場合はチェック")

            if st.button("変更を保存"):
                if delete_flag and confirm_delete:
                    ja_obj["farmers"] = [
                        f for f in ja_obj["farmers"] if f["farmer_id"] != farmer_obj["farmer_id"]
                    ]
                    save_data(data)
                    st.success(f"農家「{farmer_name}」を削除しました。")
                else:
                    farmer_obj["farmer_name"] = new_name
                    save_data(data)
                    st.success("農家名を更新しました。")

# -----------------------------
# 農地編集（名称・住所・座標・有効/無効・削除）
# -----------------------------
elif menu == "農地編集":
    st.subheader("農地編集")

    if not data["jas"]:
        st.warning("農協がありません。")
    else:
        ja_names = [j["ja_name"] for j in data["jas"]]
        ja_name = st.selectbox("農協を選択", ja_names)
        ja_obj = next(j for j in data["jas"] if j["ja_name"] == ja_name)

        if not ja_obj["farmers"]:
            st.warning("この農協には農家がありません。")
        else:
            farmer_names = [f["farmer_name"] for f in ja_obj["farmers"]]
            farmer_name = st.selectbox("農家を選択", farmer_names)
            farmer_obj = next(
                f for f in ja_obj["farmers"] if f["farmer_name"] == farmer_name
            )

            if not farmer_obj["lands"]:
                st.warning("この農家には農地がありません。")
            else:
                land_names = [l["land_name"] for l in farmer_obj["lands"]]
                land_name = st.selectbox("編集する農地を選択", land_names)
                land_obj = next(
                    l for l in farmer_obj["lands"] if l["land_name"] == land_name
                )

                new_land_name = st.text_input(
                    "農地名（編集）", value=land_obj["land_name"]
                )
                new_address = st.text_input(
                    "住所（編集）", value=land_obj.get("address", "")
                )
                new_lat = st.number_input(
                    "緯度（編集）", value=float(land_obj["lat"]), format="%.8f"
                )
                new_lon = st.number_input(
                    "経度（編集）", value=float(land_obj["lon"]), format="%.8f"
                )
                new_active = st.checkbox(
                    "有効な農地として扱う（チェックを外すと無効）",
                    value=land_obj.get("is_active", True),
                )

                delete_flag = st.checkbox("この農地を削除する")
                confirm_delete = False
                if delete_flag:
                    confirm_delete = st.checkbox("本当に削除してよい場合はチェック")

                if st.button("農地の変更を保存"):
                    if delete_flag and confirm_delete:
                        farmer_obj["lands"] = [
                            l for l in farmer_obj["lands"] if l["land_id"] != land_obj["land_id"]
                        ]
                        save_data(data)
                        st.success(f"農地「{land_name}」を削除しました。")
                    else:
                        land_obj["land_name"] = new_land_name
                        land_obj["address"] = new_address
                        land_obj["lat"] = float(new_lat)
                        land_obj["lon"] = float(new_lon)
                        land_obj["is_active"] = new_active
                        save_data(data)
                        st.success("農地情報を更新しました。")

# -----------------------------
# 農地ナビ取込（CSV/Excel）
# -----------------------------
elif menu == "農地ナビ取込":
    st.subheader("農地ナビデータ取込")

    file = st.file_uploader("CSV または Excel を選択", type=["csv", "xlsx"])

    if file is not None:
        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        st.write("読み込んだデータ")
        st.dataframe(df)

        # 想定列：農協名, 農家名, 農地住所, 緯度, 経度
        required_cols = ["農協名", "農家名", "農地住所", "緯度", "経度"]
        if not all(col in df.columns for col in required_cols):
            st.error(f"列名が足りません。必要な列: {required_cols}")
        else:
            if st.button("取込実行！"):
                for _, r in df.iterrows():
                    ja_name = str(r["農協名"])
                    farmer_name = str(r["農家名"])
                    addr = str(r["農地住所"])
                    lat = float(r["緯度"])
                    lon = float(r["経度"])

                    # 農協
                    ja_obj = next(
                        (j for j in data["jas"] if j["ja_name"] == ja_name), None
                    )
                    if not ja_obj:
                        ja_id = f"JA-{len(data['jas']) + 1:03}"
                        ja_obj = {
                            "ja_id": ja_id,
                            "ja_name": ja_name,
                            "farmers": [],
                        }
                        data["jas"].append(ja_obj)

                    # 農家
                    farmer_obj = next(
                        (f for f in ja_obj["farmers"] if f["farmer_name"] == farmer_name),
                        None,
                    )
                    if not farmer_obj:
                        farmer_id = f"FARM-{len(ja_obj['farmers']) + 1:03}"
                        farmer_obj = {
                            "farmer_id": farmer_id,
                            "farmer_name": farmer_name,
                            "lands": [],
                        }
                        ja_obj["farmers"].append(farmer_obj)

                    # 農地（住所を名前として登録）
                    land_id = f"LAND-{len(farmer_obj['lands']) + 1:03}"
                    farmer_obj["lands"].append(
                        {
                            "land_id": land_id,
                            "land_name": addr,
                            "address": addr,
                            "lat": lat,
                            "lon": lon,
                            "is_active": True,
                        }
                    )

                save_data(data)
                st.success("農地ナビデータの取込が完了しました！")
