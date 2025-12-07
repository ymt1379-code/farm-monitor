import streamlit as st
import json, os
import folium
from streamlit_folium import st_folium
import pandas as pd

DATA_FILE = "farms.json"

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"jas": []}, f)

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

st.sidebar.title("農地管理メニュー")
menu = st.sidebar.selectbox("選択してください", [
    "地図表示", "農協登録", "農家登録", "農地登録", "農地編集", "農地ナビ取込"
])

data = load_data()
st.title("農地管理クラウドシステム（β）")

# ----------------------
# 地図表示（有効農地のみ）
# ----------------------
if menu == "地図表示":
    center = [34.230532, 135.170785]  # 和歌山市役所中心
    m = folium.Map(location=center, zoom_start=13, tiles="OpenStreetMap")

    for ja in data["jas"]:
        for farmer in ja["farmers"]:
            for land in farmer["lands"]:
                if land.get("is_active", True):
                    folium.Marker(
                        [land["lat"], land["lon"]],
                        tooltip=f"{ja['ja_name']} / {farmer['farmer_name']} / {land['land_name']}"
                    ).add_to(m)

    st_folium(m, width=900, height=600)

# ----------------------
# 農協登録
# ----------------------
elif menu == "農協登録":
    ja_name = st.text_input("農協名")

    if st.button("登録"):
        ja_id = f"JA-{len(data['jas'])+1:03}"
        data["jas"].append({"ja_id": ja_id, "ja_name": ja_name, "farmers": []})
        save_data(data)
        st.success(f"{ja_name} を登録しました")

# ----------------------
# 農家登録
# ----------------------
elif menu == "農家登録":
    if not data["jas"]:
        st.warning("先に農協を登録してください")
    else:
        ja = st.selectbox("農協選択", [j["ja_name"] for j in data["jas"]])
        farmer_name = st.text_input("農家名")

        if st.button("登録"):
            for j in data["jas"]:
                if j["ja_name"] == ja:
                    farmer_id = f"FARM-{len(j['farmers'])+1:03}"
                    j["farmers"].append({"farmer_id": farmer_id, "farmer_name": farmer_name, "lands": []})
                    save_data(data)
                    st.success("農家登録完了！")

# ----------------------
# 農地登録
# ----------------------
elif menu == "農地登録":
    if not data["jas"]:
        st.warning("農協登録が必要です")
    else:
        ja = st.selectbox("農協", [j["ja_name"] for j in data["jas"]])
        ja_obj = next(j for j in data["jas"] if j["ja_name"] == ja)

        if not ja_obj["farmers"]:
            st.warning("農家が登録されていません")
        else:
            farmer = st.selectbox("農家", [f["farmer_name"] for f in ja_obj["farmers"]])
            land_name = st.text_input("農地名")
            lat = st.number_input("緯度")
            lon = st.number_input("経度")
            address = st.text_input("住所")

            if st.button("登録"):
                farmer_obj = next(f for f in ja_obj["farmers"] if f["farmer_name"] == farmer)
                land_id = f"LAND-{len(farmer_obj['lands'])+1:03}"
                farmer_obj["lands"].append({
                    "land_id": land_id,
                    "land_name": land_name,
                    "lat": lat,
                    "lon": lon,
                    "address": address,
                    "is_active": True
                })
                save_data(data)
                st.success("農地登録完了！")

# ----------------------
# 農地編集（有効/無効切替）
# ----------------------
elif menu == "農地編集":
    if not data["jas"]:
        st.warning("データがありません")
    else:
        for ja in data["jas"]:
            st.subheader(f"農協: {ja['ja_name']}")
            for farmer in ja["farmers"]:
                st.write(f"農家: {farmer['farmer_name']}")
                for land in farmer["lands"]:
                    key = f"{ja['ja_id']}-{farmer['farmer_id']}-{land['land_id']}"
                    new_state = st.checkbox(
                        f"{land['land_name']} ({land['address']})",
                        value=land.get("is_active", True),
                        key=key
                    )
                    land["is_active"] = new_state
        if st.button("保存"):
            save_data(data)
            st.success("更新しました")

# ----------------------
# 農地ナビ取込
# ----------------------
elif menu == "農地ナビ取込":
    file = st.file_uploader("CSV / Excel", type=["csv","xlsx"])
    if file:
        df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
        st.dataframe(df)

        if st.button("取込実行！"):
            for _, r in df.iterrows():
                ja_name = r["農協名"]
                farmer_name = r["農家名"]
                addr = r["農地住所"]

                ja = next((j for j in data["jas"] if j["ja_name"] == ja_name), None)
                if not ja:
                    ja_id = f"JA-{len(data['jas'])+1:03}"
                    ja = {"ja_id": ja_id, "ja_name": ja_name, "farmers": []}
                    data["jas"].append(ja)

                farmer = next((f for f in ja["farmers"] if f["farmer_name"] == farmer_name), None)
                if not farmer:
                    farmer_id = f"FARM-{len(ja['farmers'])+1:03}"
                    farmer = {"farmer_id": farmer_id, "farmer_name": farmer_name, "lands": []}
                    ja["farmers"].append(farmer)

                farmer["lands"].append({
                    "land_id": f"LAND-{len(farmer['lands'])+1:03}",
                    "land_name": addr,
                    "address": addr,
                    "lat": r["緯度"],
                    "lon": r["経度"],
                    "is_active": True
                })

            save_data(data)
            st.success("取込完了！！")
