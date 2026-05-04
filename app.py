import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("📊 Au Formal vs Au Actual Dashboard")

@st.cache_data
def load_data(file):
    df_plating = pd.read_excel(
        file, sheet_name="plating", engine="openpyxl",
        usecols=["Column1","บ่อชุบ","Miki Code","Au  Formal","จำนวน"]
    )
    df_addau = pd.read_excel(
        file, sheet_name="add au", engine="openpyxl",
        usecols=["Month","Tank","Au","remark 2"]
    )
    return df_plating, df_addau

file = st.file_uploader("Upload Excel", type=["xlsx"])
if file:
    with st.spinner("⏳ กำลังโหลดไฟล์..."):
        df_plating, df_addau = load_data(file)

    st.success("✅ โหลดไฟล์เสร็จแล้ว")

    df_plating.columns = df_plating.columns.str.strip()
    df_addau.columns = df_addau.columns.str.strip()

    # -----------------------------
    # NORMALIZE MONTH + REMARK
    # -----------------------------
    df_plating["Month"] = df_plating["Column1"].astype(str).str.strip()
    df_addau["Month"] = df_addau["Month"].astype(str).str.strip()
    df_addau["Remark"] = df_addau["remark 2"].astype(str).str.strip()

    # -----------------------------
    # FILTER (เฉพาะ Tank + Month)
    # -----------------------------
    tanks_all = df_addau["Tank"].dropna().unique().tolist()
    months_all = sorted(list(set(df_plating["Month"].dropna().unique().tolist() +
                                 df_addau["Month"].dropna().unique().tolist())))

    col1, col2 = st.columns(2)
    with col1:
        selected_tank = st.multiselect("Tank", tanks_all, default=tanks_all)
    with col2:
        selected_month = st.multiselect("Month", months_all, default=months_all)

    df_filtered_plating = df_plating[
        (df_plating["Month"].isin(selected_month)) &
        (df_plating["บ่อชุบ"].isin(selected_tank))
    ]
    df_filtered_addau = df_addau[
        (df_addau["Month"].isin(selected_month)) &
        (df_addau["Tank"].isin(selected_tank))
    ]

    # -----------------------------
    # KPI
    # -----------------------------
    st.subheader("📌 KPI Summary")
    k1, k2, k3 = st.columns(3)
    with k1:
        st.metric("Total Jobs", int(df_filtered_plating["จำนวน"].sum()))
    with k2:
        st.metric("Total Au Formal", round(df_filtered_plating["Au  Formal"].sum(), 2))
    with k3:
        st.metric("Total Au Actual", round(df_filtered_addau["Au"].sum(), 2))

    # -----------------------------
    # GRAPH SUMMARY BY TANK
    # -----------------------------
    st.subheader("📊 Au Formal vs Au Actual (by Tank)")

    df_sum_tank_formal = df_filtered_plating.groupby("บ่อชุบ", as_index=False).agg({"Au  Formal":"sum"})
    df_sum_tank_actual = df_filtered_addau.groupby("Tank", as_index=False).agg({"Au":"sum"})
    df_sum_tank_actual = df_sum_tank_actual.rename(columns={"Au":"Au Actual", "Tank":"บ่อชุบ"})

    df_compare_tank = pd.merge(df_sum_tank_formal, df_sum_tank_actual, on="บ่อชุบ", how="outer")
    df_compare_tank = df_compare_tank.sort_values("Au Actual", ascending=False)

    fig_tank = px.bar(
        df_compare_tank,
        x="บ่อชุบ",
        y=["Au  Formal","Au Actual"],
        barmode="group",
        text_auto=True,
        title="Au Formal vs Au Actual per Tank (Sorted by Au Actual)"
    )
    st.plotly_chart(fig_tank, use_container_width=True)

    # -----------------------------
    # GRAPH COMPARISON (Formal vs Actual - เฉพาะกราฟแท่ง)
    # -----------------------------
    st.subheader("📊 Au Formal vs Au Actual (by Month)")

    df_sum_formal = df_filtered_plating.groupby("Month", as_index=False).agg({"Au  Formal":"sum"})
    df_sum_actual = df_filtered_addau.groupby("Month", as_index=False).agg({"Au":"sum"})
    df_sum_actual = df_sum_actual.rename(columns={"Au":"Au Actual"})

    df_compare = pd.merge(df_sum_formal, df_sum_actual, on="Month", how="outer")

    month_order = ["Jan","Feb","March","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

    fig_bar = px.bar(
        df_compare,
        x="Month",
        y=["Au  Formal","Au Actual"],
        barmode="group",
        text_auto=True,
        category_orders={"Month": month_order},
        title="Au Formal vs Au Actual per Month"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # -----------------------------
    # GRAPH FROM ADD AU SHEET
    # -----------------------------
    st.subheader("📊 Au Actual Usage by Tank & Remark (Add Au Sheet)")

    df_addau_group = df_filtered_addau.groupby(["Remark","Month","Tank"], as_index=False).agg({"Au":"sum"})

    fig_addau = px.bar(
        df_addau_group,
        x="Month",
        y="Au",
        color="Tank",
        barmode="group",
        facet_col="Remark",
        text_auto=True,
        category_orders={"Month": month_order},
        title="Au Actual per Tank per Month (Grouped by Remark)"
    )

    fig_addau.update_xaxes(title="Month")
    fig_addau.update_yaxes(title="Au Usage")

    new_titles = {f"Remark={r}": str(r) for r in df_addau_group["Remark"].unique()}
    fig_addau.for_each_annotation(lambda a: a.update(text=new_titles.get(a.text, a.text)))

    st.plotly_chart(fig_addau, use_container_width=True)

    # -----------------------------
    # TOP 5 MIKI CODE
    # -----------------------------
    st.subheader("🏆 Top 5 Miki Code by Au Formal Usage")

    selected_month_top5 = st.selectbox("เลือกเดือนสำหรับ Top 5 (หรือไม่เลือก = รวมทั้งหมด)", ["All"] + months_all)

    if selected_month_top5 != "All":
        df_miki = df_filtered_plating[df_filtered_plating["Month"] == selected_month_top5]
    else:
        df_miki = df_filtered_plating

    df_miki = df_miki.groupby("Miki Code", as_index=False).agg({"Au  Formal":"sum"})
    df_miki_top5 = df_miki.sort_values("Au  Formal", ascending=False).head(5)

    fig_miki = px.bar(
        df_miki_top5,
        x="Miki Code",
        y="Au  Formal",
        text_auto=True,
        title=f"Top 5 Miki Code by Au Formal Usage ({selected_month_top5})"
    )
    st.plotly_chart(fig_miki, use_container_width=True)

    selected_miki_detail = st.selectbox("เลือก Miki Code เพื่อดูรายละเอียด Tank", df_miki_top5["Miki Code"].tolist())

    df_detail = df_filtered_plating[df_filtered_plating["Miki Code"] == selected_miki_detail]
    df_detail_group = df_detail.groupby("บ่อชุบ", as_index=False).agg({"จำนวน":"sum","Au  Formal":"sum"})

    st.subheader(f"📋 รายละเอียด Tank ของ Miki Code: {selected_miki_detail}")
    st.dataframe(df_detail_group)

    fig_detail = px.bar(
        df_detail_group,
        x="บ่อชุบ",
        y="Au  Formal",
        text_auto=True,
        title=f"Au Formal Usage by Tank (Miki Code: {selected_miki_detail})"
    )
    st.plotly_chart(fig_detail, use_container_width=True)
