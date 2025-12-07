import streamlit as st
import json, os
import folium
from streamlit_folium import st_folium
import pandas as pd

DATA_FILE = "farms.json"

# 初期ファイル作成
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"clients": []}, f)

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

st.title("農地管理クラウドシステム（β版）")

menu = st.sidebar.selectbox(
    "メニュー",
    ["地図表示", "顧客登録", "農地登録", "農地ナビ取込"]
)

data = load_data()

# -----------------------
# 地図表示（和歌山市役所中心）
# -----------------------
if menu == "地図表示":
    center_lat, center_lon = 34.230532, 135.170785  # 和歌山市役所
    
    map = folium.Map(location=[center_lat, center_lon], zoom_start=14, tiles="Stamen Terrain")

    # 農地が登録されていればピン表示
    for c in data["clients"]:
        for f in c["farms"]:
            folium.Marker(
                [f["lat"], f["lon"]],
                tooltip=f"{c['name']} - {f['name']}"
            ).add_to(map)

    st_folium(map, width=900, height=600)

# -----------------------
# 顧客登録
# -----------------------
elif menu == "顧客登録":
    name = st.text_input("顧客名")
    if st.button("登録"):
        data["clients"].append({"name": name, "farms": []})
        save_data(data)
        st.success("登録しました！")

# -----------------------
# 農地登録
# -----------------------
elif menu == "農地登録":
    if not data["clients"]:
        st.warning("先に顧客登録してください")
    else:
        client = st.selectbox("顧客", [c["name"] for c in data["clients"]])
        farm_name = st.text_input("農地名")
        lat = st.number_input("緯度")
        lon = st.number_input("経度")

        if st.button("保存"):
            for c in data["clients"]:
                if c["name"] == client:
                    c["farms"].append({"name": farm_name, "lat": lat, "lon": lon})
                    save_data(data)
                    st.success("農地を登録しました！")

# -----------------------
# 農地ナビデータ取込
# -----------------------
elif menu == "農地ナビ取込":
    file = st.file_uploader("CSV または Excel を選択", type=["csv", "xlsx"])

    if file:
        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        st.write("読み込みデータ", df)

        if st.button("登録実行！"):
            for _, row in df.iterrows():
                client = row["顧客名"]
                farm_name = row["農地名"]
                lat = row["緯度"]
                lon = row["経度"]

                cli = next((c for c in data["clients"] if c["name"] == client), None)
                if not cli:
                    cli = {"name": client, "farms": []}
                    data["clients"].append(cli)

                cli["farms"].append({"name": farm_name, "lat": lat, "lon": lon})

            save_data(data)
            st.success("取込が完了しました！")
