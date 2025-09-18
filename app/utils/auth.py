import streamlit as st
import pandas as pd
import bcrypt
import streamlit_authenticator as stauth
from .sheets import read_df, upsert_row

def _users_df() -> pd.DataFrame:
    df = read_df("users")
    if df.empty:
        return pd.DataFrame(columns=[
            "username","name","email","password_hash","is_admin",
            "can_news","can_weather","can_birthdays","can_videos",
            "can_worldclocks","can_currencies","active"
        ])
    return df

def build_authenticator():
    df = _users_df()
    creds = {"usernames": {}}
    for _, r in df[df["active"].astype(str).str.lower().isin(["true","1","yes"])].iterrows():
        creds["usernames"][r["username"]] = {
            "name": r["name"],
            "email": r["email"],
            "password": r["password_hash"],  # already hashed
        }
    return stauth.Authenticate(
        creds,
        st.secrets["auth"]["cookie_name"],
        st.secrets["auth"]["cookie_key"],
        st.secrets["auth"]["cookie_expiry_days"],
    )

def check_perm(username: str, perm_field: str) -> bool:
    df = _users_df()
    row = df[df["username"] == username]
    if row.empty: 
        return False
    v = str(row.iloc[0].get(perm_field, ""))
    return v.lower() in ["1","true","yes","y"]

def is_admin(username: str) -> bool:
    return check_perm(username, "is_admin")

def create_user(username: str, name: str, email: str, password_plain: str,
                is_admin_flag: bool, perms: dict):
    password_hash = bcrypt.hashpw(password_plain.encode(), bcrypt.gensalt()).decode()
    row = {
        "username": username,
        "name": name,
        "email": email,
        "password_hash": password_hash,
        "is_admin": str(bool(is_admin_flag)),
        "active": "true",
        "can_news": str(bool(perms.get("can_news", False))),
        "can_weather": str(bool(perms.get("can_weather", False))),
        "can_birthdays": str(bool(perms.get("can_birthdays", False))),
        "can_videos": str(bool(perms.get("can_videos", False))),
        "can_worldclocks": str(bool(perms.get("can_worldclocks", False))),
        "can_currencies": str(bool(perms.get("can_currencies", False))),
    }
    upsert_row("users", "username", row)

def set_password(username: str, new_password: str) -> bool:
    df = _users_df()
    idx = df.index[df["username"] == username]
    if len(idx) == 0: 
        return False
    df.loc[idx[0], "password_hash"] = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    from .sheets import replace_df
    replace_df("users", df)
    return True
