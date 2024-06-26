import re

import pandas as pd
import plotly.express as px
import streamlit as st

from crawly import Crawly, execute_task, change_update_interval
from db_handler import DbHandler

# https://stackoverflow.com/questions/3809401/what-is-a-good-regular-expression-to-match-a-url
URL_PATTERN = r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)"
REGEX_DEFAULT_PATTERN = r"[-+]?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)"
DEFAULT_UPDATE_INTERVAL = 60


def reset_checkboxes():
    st.session_state['chk_widget_idx'] += 1


def dataframe_with_selections(df):
    df_with_selections = df.copy()
    df_with_selections.insert(0, "Select", False)

    # Get dataframe row-selections from user with st.data_editor none
    edited_df = st.data_editor(
        df_with_selections,
        hide_index=True,
        column_config={"Select": st.column_config.CheckboxColumn(required=True), "name": "Name", "id": None,
                       "url": None, "xpath": None, "update_interval": None, "is_active": None, "regex": None},
        disabled=df.columns,
        use_container_width=True,
        key=f'selected_items{st.session_state["chk_widget_idx"]}'
    )

    # Filter the dataframe using the temporary column, then drop the column
    selected_rows = edited_df[edited_df.Select]
    return selected_rows.drop('Select', axis=1)


def get_tagged_element_value(row, col, default=None):
    return row[col] if row is not None and not pd.isna(row[col]) else default


def display_line_plot(df, title="", height=500):

    # only display price of point if it has changed
    df = df.sort_values(by='timestamp')
    text_values = []
    for name in df['name'].unique():
        subset_df = df[df['name'] == name]  # Get the subset of the DataFrame for the current name
        last_price = None
        trace_text = []
        # Loop through each row in the subset DataFrame
        for index, row in subset_df.iterrows():
            # Check if the current price is different from the last observed price
            if row['current_price'] != last_price:
                trace_text.append(row['current_price']) # If the price has changed, add it to the text list
                last_price = row['current_price']
            else:
                # If the price hasn't changed, add an empty string to the text list
                trace_text.append("")

        # Extend the overall text list with the text values for the current trace
        text_values.extend(trace_text)

    df['text'] = text_values    # add changed price as new col to df

    fig_price_history = px.line(df, x='timestamp', y='current_price', color='name',
                                labels={'timestamp': 'Timestamp', 'current_price': 'Current Price in €',
                                        'name': 'Tracked Element'},
                                text="text",  # Use the 'text' column for the hover text
                                height=height)
    fig_price_history.update_traces(textposition="top center")

    # Update legend to show truncated names
    for trace in fig_price_history.data:
        trace.name = (trace.name[:10] + '...') if len(trace.name) > 10 else trace.name

    fig_price_history.update_layout(title_text=title)
    st.plotly_chart(fig_price_history, use_container_width=True)


@st.cache_data
def _init_example_data():
    tracked_elem_1 = {
        'name': ["Example Product"],
        'url': ["https://example.com/product"],
        'xpath': ["//div[@class='product']"],
        'update_interval': [60],
        'is_active': [True],
        'regex': REGEX_DEFAULT_PATTERN
    }
    tracked_elem_2 = {
        'name': ["Amazon Satisfyer"],
        'url': [
            "https://www.amazon.de/-/en/Satisfyer-Generation-Warentest-technology-waterproof/dp/B071CPR2V4/ref=sr_1_1?keywords=satisfyer&qid=1704378330&sr=8-1"],
        'xpath': [
            "/html/body/div[2]/div/div[6]/div[3]/div[4]/div[13]/div/div/div[1]/div/div[3]/div[1]/span[2]/span[2]/span[2]"],
        'update_interval': [100],
        'is_active': [False],
        'regex': REGEX_DEFAULT_PATTERN
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


def one_time_track(item):
    return execute_task(-1, item)


def is_not_unique(name, df_tracked_elements, selection):
    if df_tracked_elements.empty:
        return False  # If DataFrame is empty, name is considered unique
    if not selection.empty:
        # remove selection to check whether the name is unique aside from the selection when editing an item
        filtered_df = df_tracked_elements[~df_tracked_elements['name'].isin(selection['name'])]
    else:
        filtered_df = df_tracked_elements
    return name in filtered_df['name'].values


def gui(db_handler):
    df_tracked_elements = db_handler.retrieve_tracked_elements()
    st.title('Price Tracker')

    # create a 3-column layout
    col11, col12 = st.columns([3, 1])

    with (st.container()):
        # table to select and display items
        with col12:
            selection = dataframe_with_selections(df_tracked_elements)
            col121, col122 = st.columns([1, 1])
            with col121:
                btn_delete = st.button("Delete", disabled=len(selection) != 1, use_container_width=True)
            with col122:
                btn_add = st.button("Add", on_click=reset_checkboxes, use_container_width=True)

        # graph to show price history
        with col11:
            if 'id' not in selection.columns or selection['id'].isnull().any():
                df_price_history = []
            else:
                df_price_history = db_handler.retrieve_price_history(selection['id'].tolist())

            if len(selection) > 0 and len(df_price_history) > 0:
                # merge price history with corresponding item
                merged_df = pd.merge(df_price_history, selection[['id', 'name']], left_on='tracked_elements_id',
                                     right_on='id', how='left', suffixes=('_price_history', '_selection'))

                display_line_plot(merged_df)
            else:
                empty_df = pd.DataFrame(columns=['timestamp', 'current_price', 'name'])
                if selection.empty:
                    display_line_plot(empty_df)
                else:
                    display_line_plot(empty_df, title="No tracking data yet")

        # if exactly one row is selected, we assume the user wants to edit it.
        # the data is shown in the form
        edit_row = selection.iloc()[0].copy() if len(selection) == 1 else None

        # if the user doesn't select exactly one row, we assume they want to view items in the graph, not edit them,
        # so we disable the form
        is_disabled = len(selection) > 1

        # form to add/update items
        with st.form("properties_form"):
            # Example for the name field

            name_value = "" if st.session_state['reset_form'] else get_tagged_element_value(edit_row, 'name')
            name = st.text_input("Name", max_chars=255, value=name_value, disabled=is_disabled, key='form_name')

            url_value = "" if st.session_state['reset_form'] else get_tagged_element_value(edit_row, 'url')
            url = st.text_input("URL", max_chars=2048, value=url_value, disabled=is_disabled, key='form_url')

            xpath_value = "" if st.session_state['reset_form'] else get_tagged_element_value(edit_row, 'xpath')
            xpath = st.text_area("CSS Selector (recommended) / XPATH",
                                 value=xpath_value, disabled=is_disabled,
                                 help="To retrieve the CSS selector, go to the item's page, right-click on the price element -> Inspect. Right-click on the html element "
                                      "that selects the price -> Copy -> CSS Selector.", key='form_xpath')

            regex_value = "" if st.session_state['reset_form'] else get_tagged_element_value(edit_row, 'regex')
            regex = st.text_area("Regex (leave empty for default value)",
                                 value=regex_value, disabled=is_disabled,
                                 placeholder=REGEX_DEFAULT_PATTERN,
                                 help="The regular expression helps to select the price element and convert it to a number.",
                                 key='form_regex')

            # Adding input fields for update interval, min price, max price, and a checkbox for active
            col211, col212, col213 = st.columns([1, 1, 1])

            with col211:
                update_interval_value = DEFAULT_UPDATE_INTERVAL if st.session_state['reset_form'] else get_tagged_element_value(edit_row, 'update_interval', DEFAULT_UPDATE_INTERVAL)
                update_interval = st.number_input("Update Interval (in minutes)",
                                                  value=update_interval_value,
                                                  min_value=1, max_value=(60 * 24 * 7),
                                                  disabled=is_disabled,
                                                  key='form_update_interval')

            is_active_value = True if st.session_state['reset_form'] else get_tagged_element_value(edit_row, 'is_active', default=True)
            is_active = st.toggle("Active", value=is_active_value,
                                  disabled=is_disabled)

            btn_save = st.form_submit_button("Save", disabled=is_disabled)


        if btn_delete:
            with st.spinner('Loading...'):
                st.write(f"Delete item: {selection['name']}")
                print(f"Delete item: {selection['name']}")
                ids = selection['id'].tolist()
                db_handler.delete_tracked_element_by_id(ids)
                st.rerun()  # necessary to update the selection list

        if btn_save:
            with st.spinner('Loading...'):
                if url is None or not re.findall(URL_PATTERN, url):
                    st.error("Please enter a valid URL")
                elif is_not_unique(name, df_tracked_elements, selection):  # name needs to be unique for displaying the items in the graph properly
                    st.error("Please enter a unique name")
                else:
                    form_data = {
                        'id': get_tagged_element_value(edit_row, "id", -1),
                        'name': name,
                        'url': url,
                        'xpath': xpath,
                        'regex': regex.strip() if regex and regex.strip() else REGEX_DEFAULT_PATTERN,  # use placeholder value if nothing else was specified
                        'update_interval': update_interval,
                        'is_active': is_active
                    }

                    # if this works, the item is already inserted in the db here
                    # if not, it returns -1
                    extracted_price = one_time_track(form_data)

                    if extracted_price == -1:
                        st.error("Failed extracting a price. Please change your parameters")
                    else:
                        df = pd.DataFrame([form_data])

                        if len(selection) == 1:     # update selected item
                            id_ = int(selection['id'].values[0])
                            db_handler.update_tracked_element(id_, df)
                            change_update_interval(db_handler.retrieve_tracked_element_by_id(id_))
                            st.write(f'Updated element {name}')
                        else:  # form is disabled if there is more than 1 selection, so this means no selections -> insert new item
                            # item has already been inserted by crawly at this point
                            st.write(f"Inserted element {df['name']}")
                            st.session_state['reset_form'] = True
                        st.rerun()  # necessary to update the selection list

    with st.container():
        st.write('Authors: Michael Duschek, Carina Hauber, Lukas Seifriedsberger, 2024')


# starts the web crawler (in an own daemon thread)
# st.cache_data prevents this to be executed on every page reload
@st.cache_data
def start_crawly(_db_handler):
    print("STARTING CRAWLY")
    scheduler = Crawly(_db_handler)
    scheduler.run()


if __name__ == '__main__':
    st.set_page_config(layout="wide")

    if 'chk_widget_idx' not in st.session_state:
        st.session_state['chk_widget_idx'] = 0

    if 'reset_form' not in st.session_state:
        st.session_state['reset_form'] = False

    db_handler = DbHandler()
    if db_handler.conn is None:
        db_handler.init_db()

    start_crawly(db_handler)
    gui(db_handler)

    if st.session_state['reset_form']:
        st.session_state['reset_form'] = False
