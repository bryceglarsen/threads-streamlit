# streamlit_app.py

import streamlit as st
import psycopg2
from pandas import DataFrame

# Initialize connection.
# Uses st.cache_resource to only run once.
@st.cache_resource
def init_connection():
    return psycopg2.connect(**st.secrets["postgres"])


def add_data(conn, twitter_entry, threads_entry):
    query = f"""
        INSERT INTO public.twitter_to_threads(twitter, threads)
        VALUES ('{twitter_entry}', '{threads_entry}');
    """
    with conn.cursor() as cur:
        cur.execute(query)
        conn.commit()
    return


@st.cache_data(ttl=600)
def get_data(_conn):
    with _conn.cursor() as cur:
        cur.execute('SELECT twitter, threads FROM public.twitter_to_threads_latest')
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        df = DataFrame(rows, columns=columns)
        df['twitter_link'] = 'https://twitter.com/' + df['twitter'].astype(str)
        df['threads_link'] = 'https://threads.net/' + df['threads'].astype(str)
        return df


def main():
    conn = init_connection()

    tab1, tab2 = st.tabs(["Add Entry", "Find Others"])

    with tab1:
        with st.form("form", True):
            st.write("Twitter to Threads")
            col1, col2 = st.columns([1,1])
            with col1:
                twitter = st.text_input("Twitter", placeholder="@", key='twitter_entry')
            with col2:
                threads = st.text_input("Threads", placeholder="@", key='threads_entry')
            add = st.form_submit_button('add')

        if add:
            if twitter and threads:
                add_data(conn, twitter, threads)
                st.success('Added!')
            else:
                st.error('Both fields are required.')
    
    with tab2:
        df_data = get_data(conn)

        def clear_search():
            st.session_state.handle = ""

        with st.form("search"):
            col1, col2, col3, col4 = st.columns([1,2,1,1])
            with col1:
                platform = st.radio("Platform", ["twitter", "threads"])
            with col2:
                handle = st.text_input("Handle", placeholder="@", key="handle")
            with col4:
                search = st.form_submit_button('search')

        if search:
            if platform and handle:
                df_data = df_data[df_data[platform] == handle]
            else:
                st.error('Please include hande.')
        
        if handle:
            clear = st.button("clear", on_click=clear_search)

        df_display = df_data[["twitter_link", "threads_link"]]
        st.dataframe(        
            df_display, 
            column_config={
                "twitter_link": st.column_config.LinkColumn(
                    label="twitter",
                    help="Double click entry for hyperlink",
                ),
                "threads_link": st.column_config.LinkColumn(
                    label="threads",
                    help="Double click entry for hyperlink",
                )
            },
            hide_index=True, 
            use_container_width=True
        )

    

if __name__ == '__main__':
    main()