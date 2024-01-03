import pandas as pd
import streamlit as st
from db_handler import DbHandler
import plotly.express as px


def main():
    db_handler = DbHandler()
    if db_handler.conn is None:
        db_handler.init_db()

    # data1 = {
    #     'name': ["Example Product"],
    #     'domain_name': ["example.com"],
    #     'url': ["https://example.com/product"],
    #     'xpath': ["//div[@class='product']"],
    #     'update_interval': [60],
    #     'min_price_threshold': [50.0],
    #     'max_price_threshold': [100.0],
    #     'is_active': [True],
    #     'notify': [True]
    # }
    #
    # df1 = pd.DataFrame(data1)
    # db_handler.insert_tracked_element(df1)
    #
    # data2 = {
    #     'tracked_elements_id': [1],
    #     'current_price': [100.99],
    #     'timestamp': ['2024-01-01 12:00:00']
    # }
    #
    # # Creating a sample DataFrame
    # df2 = pd.DataFrame(data2)
    # db_handler.insert_price_history(df2)


    df_tracked_elements = db_handler.retrieve_tracked_elements()

    df_price_history = db_handler.retrieve_price_history(1)

    ####################################################################################################################

    df_price_history['timestamp'] = pd.to_datetime(df_price_history['timestamp'])

    # Create a line plot using Plotly
    fig_price_history = px.line(df_price_history, x='timestamp', y='current_price', color='tracked_elements_id',

                  labels={'timestamp': 'Timestamp', 'current_price': 'Current Price in €',
                          'tracked_elements_id': 'Tracked Element'})

    ####################################################################################################################
    # Streamlit app
    st.set_page_config(layout="wide")
    st.title('Price Tracker')

    # Create a 3-column layout
    col11, col12 = st.columns([3, 1])
    col21, col22 = st.columns([3, 1])

    with st.container():
        with col11:
            # st.write(df_price_history)
            st.plotly_chart(fig_price_history, use_container_width=True)
        with col12:
            st.write(df_tracked_elements)
            btn_add = st.button('Add', use_container_width=True)

    # properties
    with st.container():
        with col21:
            with st.form("properties_form"):
                url = st.text_input("URL")
                xpath = st.text_area("XPATH")

                # Adding input fields for update interval, min price, max price, and a checkbox for active
                col211, col212, col213 = st.columns([1, 1, 1])
                # use_thresholds = False

                use_thresholds = st.empty()  # Placeholder

                with col211:
                    update_interval = st.number_input("Update Interval (in minutes)", value=60, min_value=1)
                with col212:
                    min_price = st.empty()
                with col213:
                    max_price = st.empty()

                notify = st.toggle("Notify me via email", value=True)
                is_active = st.toggle("Active", value=True)

                # col1, col2 = st.ro

                btn_delete = st.form_submit_button("Delete")
                btn_save = st.form_submit_button("Save")

            with use_thresholds:
                use_thresholds = st.toggle("Use Thresholds", value=False,
                                           help="If this is disabled, you will be notified on every price change IF 'Notify me via email' is also set")

            with col212:
                with min_price:
                    if use_thresholds:
                        min_price = st.number_input("Min Price", value=0.0, step=1.0, min_value=0.0, disabled=False,
                                                    help="Maximum threshold for the price. You will be notified when this is crossed.")
                    else:
                        min_price = st.number_input("Min Price", value=0.0, step=1.0, min_value=0.0, disabled=True,
                                                   help="Maximum threshold for the price. You will be notified when this is crossed.")
            with col213:
                with max_price:
                    if use_thresholds:
                        max_price = st.number_input("Max Price", value=100.0, step=1.0, min_value=0.0, disabled=False,
                                                    help="Maximum threshold for the price. You will be notified when this is crossed.")
                    else:
                        max_price = st.number_input("Max Price", value=100.0, step=1.0, min_value=0.0, disabled=True,
                                                    help="Maximum threshold for the price. You will be notified when this is crossed.")

    with st.container():
        st.write('Authors: Michael Duschek, Carina Hauber, Lukas Seifriedsberger, 2024')


    # db_handler.close_db()


if __name__ == '__main__':
    main()
