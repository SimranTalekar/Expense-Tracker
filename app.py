"""
Expense Tracker - Streamlit Frontend
Run locally:  streamlit run app.py
"""

from datetime import date, datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from backend import CATEGORIES, DATE_FORMAT, Storage, User

st.set_page_config(page_title="Expense Tracker", page_icon="💸", layout="wide")

# ---------- Styling ----------
st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; max-width: 1200px;}
    .hero {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%);
        padding: 1.6rem 2rem; border-radius: 18px; color: white; margin-bottom: 1.2rem;
        box-shadow: 0 8px 24px rgba(99,102,241,.35);
    }
    .hero h1 {margin: 0; font-size: 2.1rem; color: white;}
    .hero p {margin: .3rem 0 0 0; opacity: .9;}
    div[data-testid="stMetric"] {
        background: rgba(139,92,246,.10); border: 1px solid rgba(139,92,246,.30);
        padding: 1rem 1.2rem; border-radius: 14px;
    }
    .stButton > button, .stFormSubmitButton > button {
        border-radius: 10px; font-weight: 600;
    }
    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)


def rupees(x) -> str:
    return f"₹{x:,.0f}"


def to_df(expenses: list) -> pd.DataFrame:
    df = pd.DataFrame(expenses, columns=["ID", "Date", "Category", "Amount", "Description"])
    df["DateParsed"] = pd.to_datetime(df["Date"], format=DATE_FORMAT, errors="coerce")
    df["Label"] = df["Category"].map(lambda c: f"{CATEGORIES.get(c, '🧾')} {c}")
    return df


# ---------- Sidebar: profile + budget ----------
with st.sidebar:
    st.markdown("## 👤 Your Profile")
    username = st.text_input(
        "Your name / ID", value=st.session_state.get("username", "guest"),
        help="Your data is saved under this name. Use the same name next time to get it back.",
    )
    st.session_state["username"] = username

    user = User(Storage(username))

    st.markdown("## 🎯 Monthly Budget")
    new_budget = st.number_input("Budget (₹)", min_value=0, step=500, value=user.budget)
    if st.button("💾 Set Budget", use_container_width=True):
        user.set_budget(new_budget)
        st.toast("Budget successfully set!", icon="✅")
        st.rerun()

    st.divider()
    st.caption("💡 Tip: use a unique name so your data stays separate from others.")

# ---------- Header ----------
st.markdown(
    f"""
    <div class="hero">
        <h1>💸 Expense Tracker</h1>
        <p>Welcome, <b>{username or 'guest'}</b> — track every rupee, stay within budget.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

today = date.today()
month_spent = user.month_spending(today.year, today.month)
remaining = user.remaining()

tab_dash, tab_add, tab_hist, tab_ana = st.tabs(
    ["📊 Dashboard", "➕ Add Expense", "📜 History", "📈 Analytics"]
)

# ---------- Dashboard ----------
with tab_dash:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🎯 Monthly Budget", rupees(user.budget))
    c2.metric("🔥 Spent This Month", rupees(month_spent))
    c3.metric("💰 Remaining", rupees(remaining))
    c4.metric("🧮 Total Spendings", rupees(user.total_spending()))

    if user.budget > 0:
        pct = month_spent / user.budget
        st.progress(min(pct, 1.0), text=f"{pct * 100:.0f}% of this month's budget used")
        if pct >= 1:
            st.error("🚨 You've exceeded your monthly budget!")
        elif pct >= 0.8:
            st.warning("⚠️ You've used over 80% of your budget.")
    else:
        st.info("👈 Set your monthly budget from the sidebar to see progress here.")

    left, right = st.columns([1, 1])
    cat = user.category_spending()
    with left:
        st.subheader("🗂️ Category-Wise Spending")
        if sum(cat.values()) == 0:
            st.info("No expenses yet. Add your first one! ➕")
        else:
            cat_df = pd.DataFrame(
                {"Category": [f"{CATEGORIES[k]} {k}" for k in cat], "Amount": list(cat.values())}
            )
            fig = px.pie(cat_df[cat_df["Amount"] > 0], names="Category", values="Amount", hole=0.55)
            fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=330)
            st.plotly_chart(fig, use_container_width=True)
    with right:
        st.subheader("🕒 Recent Expenses")
        if user.expenses:
            df = to_df(user.expenses).sort_values("DateParsed", ascending=False).head(6)
            st.dataframe(
                df[["Date", "Label", "Amount", "Description"]].rename(columns={"Label": "Category"}),
                hide_index=True, use_container_width=True,
            )
        else:
            st.info("Nothing here yet.")

# ---------- Add Expense ----------
with tab_add:
    st.subheader("➕ Add a New Expense")
    with st.form("add_expense", clear_on_submit=True):
        a, b = st.columns(2)
        exp_date = a.date_input("📅 Date", value=today, format="DD/MM/YYYY")
        category = b.selectbox("🏷️ Category", list(CATEGORIES), format_func=lambda c: f"{CATEGORIES[c]} {c}")
        amount = a.number_input("💵 Amount (₹)", min_value=1, step=10, value=100)
        description = b.text_input("📝 Description", placeholder="e.g. Lunch with friends")
        submitted = st.form_submit_button("✅ Add Expense", use_container_width=True)

    if submitted:
        try:
            user.add_expense(exp_date, category, amount, description)
            st.toast("Expense successfully added !!", icon="🎉")
            st.rerun()
        except ValueError as err:
            st.error(str(err))

# ---------- History ----------
with tab_hist:
    st.subheader("📜 All Expenses")
    if not user.expenses:
        st.info("No expenses recorded yet.")
    else:
        df = to_df(user.expenses).sort_values("DateParsed", ascending=False)

        f1, f2 = st.columns([2, 1])
        search = f1.text_input("🔍 Search description", "")
        picked = f2.multiselect("Filter category", list(CATEGORIES), default=[])

        view = df
        if search:
            view = view[view["Description"].str.contains(search, case=False, na=False)]
        if picked:
            view = view[view["Category"].isin(picked)]

        st.dataframe(
            view[["Date", "Label", "Amount", "Description"]].rename(columns={"Label": "Category"}),
            hide_index=True, use_container_width=True,
        )
        st.caption(f"Showing {len(view)} of {len(df)} expenses — total {rupees(view['Amount'].sum())}")

        d1, d2 = st.columns([3, 1])
        with d1:
            options = {
                row.ID: f"{row.Date} · {row.Category} · ₹{row.Amount} · {row.Description or '-'}"
                for row in view.itertuples()
            }
            to_delete = st.selectbox(
                "🗑️ Delete an expense", options=list(options), format_func=lambda i: options[i],
                index=None, placeholder="Choose an expense...",
            ) if options else None
        with d2:
            st.write("")
            st.write("")
            if st.button("Delete", disabled=to_delete is None, use_container_width=True):
                user.delete_expense(to_delete)
                st.toast("Expense deleted", icon="🗑️")
                st.rerun()

        st.download_button(
            "⬇️ Download as CSV",
            df[["Date", "Category", "Amount", "Description"]].to_csv(index=False),
            file_name="expenses.csv", mime="text/csv",
        )

# ---------- Analytics ----------
with tab_ana:
    st.subheader("📈 Spending Trends")
    if not user.expenses:
        st.info("Add some expenses to see trends.")
    else:
        df = to_df(user.expenses).dropna(subset=["DateParsed"])
        if df.empty:
            st.info("No valid dates found.")
        else:
            col1, col2 = st.columns(2)
            monthly = df.groupby(df["DateParsed"].dt.to_period("M").astype(str))["Amount"].sum().reset_index()
            monthly.columns = ["Month", "Amount"]
            fig1 = px.bar(monthly, x="Month", y="Amount", title="Monthly Spending", text_auto=True)
            col1.plotly_chart(fig1, use_container_width=True)

            daily = df.groupby("DateParsed")["Amount"].sum().reset_index()
            fig2 = px.line(daily, x="DateParsed", y="Amount", markers=True, title="Daily Spending")
            fig2.update_xaxes(title="Date")
            col2.plotly_chart(fig2, use_container_width=True)

            by_cat = df.groupby("Label")["Amount"].sum().sort_values().reset_index()
            fig3 = px.bar(by_cat, x="Amount", y="Label", orientation="h", title="By Category", text_auto=True)
            fig3.update_yaxes(title="")
            st.plotly_chart(fig3, use_container_width=True)

st.caption("Made with ❤️ using Streamlit")
