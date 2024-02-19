import pandas as pd
import streamlit as st
import threading
from crawly import Crawly
from db_handler import DbHandler
import plotly.express as px
import re

# https://stackoverflow.com/questions/3809401/what-is-a-good-regular-expression-to-match-a-url
URL_PATTERN = r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)"


def dataframe_with_selections(df):
    df_with_selections = df.copy()
    df_with_selections.insert(0, "Select", False)

    # Get dataframe row-selections from user with st.data_editor none
    edited_df = st.data_editor(
        df_with_selections,
        hide_index=True,
        column_config={"Select": st.column_config.CheckboxColumn(required=True), "name": "Name", "id": None,
                       "url": None, "xpath": None, "update_interval": None, "min_price_threshold": None,
                       "max_price_threshold": None, "is_active": None, "notify": None},
        disabled=df.columns,
        use_container_width=True,
    )

    # Filter the dataframe using the temporary column, then drop the column
    selected_rows = edited_df[edited_df.Select]
    return selected_rows.drop('Select', axis=1)


def get_tagged_element_value(row, col, default=None):
    return row[col] if row is not None and not pd.isna(row[col]) else default


def display_line_plot(df, title="", height=500):
    fig_price_history = px.line(df, x='timestamp', y='current_price', color='name',
                                labels={'timestamp': 'Timestamp', 'current_price': 'Current Price in €',
                                        'name': 'Tracked Element'},
                                text="current_price",
                                height=height)
    fig_price_history.update_traces(textposition="top center")
    fig_price_history.update_layout(title_text=title)
    st.plotly_chart(fig_price_history, use_container_width=True)


@st.cache_data
def _init_example_data():
    tracked_elem_1 = {
        'name': ["Example Product"],
        'url': ["https://example.com/product"],
        'xpath': ["//div[@class='product']"],
        'update_interval': [60],
        'min_price_threshold': [50.0],
        'max_price_threshold': [100.0],
        'is_active': [True],
        'notify': [True]
    }
    tracked_elem_2 = {
        'name': ["Amazon Satisfyer"],
        'url': [
            "https://www.amazon.de/-/en/Satisfyer-Generation-Warentest-technology-waterproof/dp/B071CPR2V4/ref=sr_1_1?keywords=satisfyer&qid=1704378330&sr=8-1"],
        'xpath': [
            "/html/body/div[2]/div/div[6]/div[3]/div[4]/div[13]/div/div/div[1]/div/div[3]/div[1]/span[2]/span[2]/span[2]"],
        'update_interval': [100],
        'min_price_threshold': [69.0],
        'max_price_threshold': None,
        'is_active': [False],
        'notify': [False]
    }
    df1 = pd.DataFrame(tracked_elem_1)
    df2 = pd.DataFrame(tracked_elem_2)
    db_handler.insert_tracked_element(df1)
    db_handler.insert_tracked_element(df2)

    price_history_1 = [
        {
        'tracked_elements_id': [1],
        'current_price': [100.99],
        'timestamp': ['2024-01-01 12:00:00']
        },
        {
            'tracked_elements_id': [1],
            'current_price': [69.69],
            'timestamp': ['2024-01-01 13:12:12']
        },
        {
            'tracked_elements_id': [1],
            'current_price': [420.10],
            'timestamp': ['2024-01-01 14:26:59']
        }
    ]
    price_history_2 = [
        {
            'tracked_elements_id': [2],
            'current_price': [35.44],
            'timestamp': ['2024-01-04 15:27:23']
        },
        {
            'tracked_elements_id': [2],
            'current_price': [26.78],
            'timestamp': ['2024-01-04 19:27:23']
        },
        {
            'tracked_elements_id': [2],
            'current_price': [69.99],
            'timestamp': ['2024-01-04 22:15:23']
        },
    ]

    # Creating a sample DataFrame
    for history in price_history_1:
        df = pd.DataFrame(history)
        db_handler.insert_price_history(df)

    for history in price_history_2:
        df = pd.DataFrame(history)
        db_handler.insert_price_history(df)


def reset_checkboxes():
    pass
    #df_with_selections['Select'] = False
    #st.session_state["p"] = False
# TODO: selection does not yet unselect all items properly in the GUI


def main(db_handler):
    selected_element = None

    # _init_example_data()

    df_tracked_elements = db_handler.retrieve_tracked_elements()


    #print(df_price_history)
    ####################################################################################################################


    # Create a line plot using Plotly
    # fig_price_history = px.line(df_price_history, x='timestamp', y='current_price', color='tracked_elements_id',
    #
    #                             labels={'timestamp': 'Timestamp', 'current_price': 'Current Price in €',
    #                                     'tracked_elements_id': 'Tracked Element'})

    ####################################################################################################################
    # Streamlit app

    st.title('Price Tracker')
    # Create a 3-column layout
    col11, col12 = st.columns([3, 1])
    # col21, col22 = st.columns([3, 0])

    # properties
    with st.container():
        with col12:
            # select_df, selection = dataframe_with_selections(df_tracked_elements)
            btn_add = st.button('Add', use_container_width=True, on_click=reset_checkboxes)
            selection = dataframe_with_selections(df_tracked_elements)

            # if btn_add:
                # TODO: selection does not yet unselect all items properly in the GUI
                # dataframe_with_selections(df_tracked_elements)
                # selection = selection.iloc[0:0]
                # select_df["Select"] = False
                # st.write(select_df)
            # st.write(selection)
        with col11:
            df_price_history = db_handler.retrieve_price_history(selection['id'].tolist())
            if not selection.empty and not df_price_history.empty:
                merged_df = pd.merge(df_price_history, selection[['id', 'name']], left_on='tracked_elements_id', right_on='id',
                                     how='left')

                # TODO: truncate the names of the products in the legend
                # merged_df['name'] = merged_df['name'].apply(
                #     lambda name: name[:10] + '...' if len(name) > 10 else name)

                display_line_plot(merged_df)
            else:
                empty_df = pd.DataFrame(columns=['timestamp', 'current_price', 'name'])
                if selection.empty:
                    display_line_plot(empty_df)
                else:
                    display_line_plot(empty_df, title="No tracking data yet")

        edit_row = selection.iloc()[0].copy() if len(selection) == 1 else None
        disabled = len(selection) > 1
        with st.form("properties_form"):
            name = st.text_input("Name", max_chars=255, value=get_tagged_element_value(edit_row, 'name'), disabled=disabled)
            url = st.text_input("URL", max_chars=2048, value=get_tagged_element_value(edit_row, 'url'), disabled=disabled)
            xpath = st.text_area("XPATH", value=get_tagged_element_value(edit_row, 'xpath'), disabled=disabled)

            # Adding input fields for update interval, min price, max price, and a checkbox for active
            col211, col212, col213 = st.columns([1, 1, 1])

            use_thresholds = st.empty()  # Placeholder

            with col211:
                update_interval = st.number_input("Update Interval (in minutes)",
                                                  value=get_tagged_element_value(edit_row, 'update_interval'),
                                                  min_value=1, max_value=(60 * 24 * 7),
                                                  disabled=disabled)
            with col212:
                min_price = st.empty()
            with col213:
                max_price = st.empty()

            notify = st.toggle("Notify me via email", value=get_tagged_element_value(edit_row, 'notify', default=True), disabled=disabled)
            is_active = st.toggle("Active", value=get_tagged_element_value(edit_row, 'is_active', default=True), disabled=disabled)

            btn_delete = st.form_submit_button("Delete", disabled=len(selection) != 1)
            btn_save = st.form_submit_button("Save", disabled=disabled)

        with use_thresholds:
            use_thresholds = st.toggle("Use Thresholds", value=get_tagged_element_value(edit_row, 'min_price_threshold') or get_tagged_element_value(edit_row, 'max_price_threshold'), disabled=disabled,
                                       help="If this is disabled, you will be notified on every price change IF 'Notify me via email' is also set")

        with col212:
            with min_price:
                min_price = st.number_input("Min Price", value=get_tagged_element_value(edit_row, 'min_price_threshold'), step=1.0, min_value=0.0, disabled=not use_thresholds or disabled,
                                            help="Maximum threshold for the price. You will be notified when this is crossed.")
        with col213:
            with max_price:
                max_price = st.number_input("Max Price", value=get_tagged_element_value(edit_row, 'max_price_threshold'), step=1.0, min_value=0.0, disabled=not use_thresholds or disabled,
                                            help="Maximum threshold for the price. You will be notified when this is crossed.")

        if btn_save:
            if url is None or not re.findall(URL_PATTERN, url):
                st.error("Please enter a valid URL")
            else:
                form_data = {
                    'name': name,
                    'url': url,
                    'xpath': xpath,
                    'update_interval': update_interval,
                    'min_price_threshold': None,
                    'max_price_threshold': None,
                    'notify': notify,
                    'is_active': is_active
                }
            if min_price != st.empty():
                form_data['min_price_threshold'] = min_price
                form_data['max_price_threshold'] = max_price

                df = pd.DataFrame([form_data])
                if len(selection) == 1:
                    st.write(f'Update element {name}')
                    id_ = int(selection['id'].values[0])
                    db_handler.update_tracked_element(id_, df)
                else:   # form is disabled if there is more than 1 selection, so this means no selections
                    st.write(f"Insert element {df['name']}")
                    db_handler.insert_tracked_element(df)
                    st.experimental_rerun()     # necessary to update the selection list

        if btn_delete:
            st.write(f"Delete item: {selection['name']}")
            ids = selection['id'].tolist()
            db_handler.delete_tracked_element_by_id(ids)
            st.experimental_rerun()     # necessary to update the selection list


    with st.container():
        st.write('Authors: Michael Duschek, Carina Hauber, Lukas Seifriedsberger, 2024')


# starts the web crawler (in an own daemon thread)
# st.cache_data prevents this to be executed on every page reload
@st.cache_data
def start_crawly(_db_handler):
    print("RUN CRAWLY!")
    scheduler = Crawly(_db_handler)
    scheduler.run()


if __name__ == '__main__':
    # print("Start GUI")
    st.set_page_config(layout="wide")

    db_handler = DbHandler()
    if db_handler.conn is None:
        db_handler.init_db()

    # start_crawly(db_handler)
    main(db_handler)

