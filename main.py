# Import python packages

import streamlit as st

from snowflake.snowpark.context import get_active_session

from snowflake.snowpark.functions import col, when_matched, when_not_matched, current_timestamp

import pandas as pd

import random

from PIL import Image

import math

import re

 

# sets the screen to display on widescreen without being confined to a container

st.set_page_config(layout="wide")

 

# gets the session for connection to databases

session = get_active_session()

 

# use to get user info for users changing categories

def get_user_info():

    user = str(st.experimental_user.email)

    user = user.split("@")

    user = user[0].upper()

    user = user.replace(".", "_")

    return user

 

# function for displaying a certain amount of rows on a page

def split_frame(input_df, rows):

    df = [input_df.loc[i: i + rows - 1, :] for i in range(0, len(input_df), rows)]

    return df

 

# Define the session state variable for the current page if it's not already set

if 'current_page' not in st.session_state:

    st.session_state['current_page'] = 'home'

 

if 'key_category_id' not in st.session_state:

    # if not, initialize it with a default value

    st.session_state['key_category_id'] = 1

 

if 'editID' not in st.session_state:

    st.session_state.editID = None

 

# function to change the current matrix category to load in

def change_key_val(key_val):

    st.session_state['key_category_id'] = key_val

 

def change_page_and_val(page_name, key_val):

    st.session_state['current_page'] = page_name

    st.session_state['key_category_id'] = key_val

 

# Function to change the page

def change_page(page: str, editID=None):

    if editID is not None:

        st.session_state.editID = editID

 

    st.session_state['current_page'] = page

 

# for deleting regional subs

def delete_sub(subscription_id):

    st.session_state.delete_subscription_id = subscription_id

 

# error handling/user error to prevent accidental deletions

def delete_confirm(delete_flag, subscription_id=None):

    session = get_active_session()

 

    if delete_flag == 1:

        query = session.sql(f"SELECT * FROM USLA_REGIONAL_SUBSCRIPTIONS WHERE SUBSCRIPTION_ID = {subscription_id}").collect()

        update_subscriptions_audit(query, get_user_info(), "Delete")

        delete_sql = "DELETE FROM USLA_REGIONAL_SUBSCRIPTIONS WHERE SUBSCRIPTION_ID = " + str(subscription_id)

        run = session.sql(delete_sql)

        run.collect()

       

    del st.session_state.delete_subscription_id

   

    

 

# method for adding regional subscriptions

def add_reg_sub(session, branch_number, service_center_long_name, manager_name,

               manager_email, employee_number, is_regional_manager):

 

    no_errors = True

 

    # Make a regular expression for validating email

    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'

 

    if not (re.fullmatch(regex, manager_email)):

        st.error("Please input a valid Email")

        no_errors = False

   

    if len(branch_number) == 0:

        st.error("Please input a Branch Number")

        no_errors = False

    if len(service_center_long_name) == 0:

        st.error("Please input a Service Center")

        no_errors = False

    if len(manager_name) == 0:

        st.error("Please input a Manager Name")

        no_errors = False

    if len(manager_email) == 0:

        st.error("Please input a Manager Email")

        no_errors = False

    if len(employee_number) == 0:

        st.error("Please input a Employee Number")

        no_errors = False

 

    try:

        int(employee_number)

    except:

        st.error("Employee number must be numeric!")

        no_errors = False

 

    try:

        int(branch_number)

    except:

        st.error("Branch number must be numeric!")

        no_errors = False

 

    if no_errors:

 

        lastchangedby = get_user_info()

        existing_ids = session.sql("SELECT SUBSCRIPTION_ID FROM USLA_REGIONAL_SUBSCRIPTIONS").collect()

        existing_ids_list = [row.SUBSCRIPTION_ID for row in existing_ids]

        if st.session_state.editID not in existing_ids_list:

            subscription_id = random.randint(1000, 9999)

            while subscription_id in existing_ids_list:

                subscription_id = random.randint(1000, 9999)

            createdby = get_user_info()

            sub_info = (subscription_id, branch_number, service_center_long_name, manager_name, manager_email, employee_number, is_regional_manager)

            update_subscriptions_audit(sub_info, createdby, "Create")

        else:

            subscription_id = st.session_state.editID

            search_createdby = session.sql("SELECT CREATEDBY FROM USLA_REGIONAL_SUBSCRIPTIONS WHERE SUBSCRIPTION_ID = " + str(subscription_id)).collect()

            createdby = str(search_createdby[0]["CREATEDBY"])

            sub_info = (subscription_id, branch_number, service_center_long_name, manager_name, manager_email, employee_number, is_regional_manager)

            update_subscriptions_audit(sub_info, lastchangedby, "Update")

       

        source_df = (session.create_dataframe(

            [

                [

                    subscription_id,

                    branch_number,

                    service_center_long_name,

                    manager_name,

                    manager_email,

                    employee_number,

                    is_regional_manager,

                    createdby,

                    lastchangedby,

                ]

            ],

            schema=["SUBSCRIPTION_ID", "SERVICE_CENTER_BRANCH_NUMBER", "SERVICE_CENTER_LONG_NAME",

                   "MANAGER_NAME", "MANAGER_EMAIL", "EMPLOYEE_NUMBER", "IS_REGIONAL_MANAGER",

                   "CREATEDBY", "LASTCHANGEDBY"]

        ).with_column("CREATEDDATE", current_timestamp())

                     .with_column("LASTCHANGEDDATE", current_timestamp()))

   

        target_df = session.table("USLA_REGIONAL_SUBSCRIPTIONS")

        target_df.merge(

            source_df,

            (target_df["SUBSCRIPTION_ID"] == source_df["SUBSCRIPTION_ID"]),

            [

                when_matched().update(

                        {

                            "SUBSCRIPTION_ID": source_df["SUBSCRIPTION_ID"],

                            "SERVICE_CENTER_BRANCH_NUMBER": source_df["SERVICE_CENTER_BRANCH_NUMBER"],

                            "SERVICE_CENTER_LONG_NAME": source_df["SERVICE_CENTER_LONG_NAME"],

                            "MANAGER_NAME": source_df["MANAGER_NAME"],

                            "MANAGER_EMAIL": source_df["MANAGER_EMAIL"],

                            "EMPLOYEE_NUMBER": source_df["EMPLOYEE_NUMBER"],

                            "IS_REGIONAL_MANAGER": source_df["IS_REGIONAL_MANAGER"],

                            "CREATEDBY": source_df["CREATEDBY"],

                            "CREATEDDATE": source_df["CREATEDDATE"],

                            "LASTCHANGEDBY": source_df["LASTCHANGEDBY"],

                            "LASTCHANGEDDATE": source_df["LASTCHANGEDDATE"],

                        }

                    ),

                    when_not_matched().insert(

                        {

                            "SUBSCRIPTION_ID": source_df["SUBSCRIPTION_ID"],

                            "SERVICE_CENTER_BRANCH_NUMBER": source_df["SERVICE_CENTER_BRANCH_NUMBER"],

                            "SERVICE_CENTER_LONG_NAME": source_df["SERVICE_CENTER_LONG_NAME"],

                            "MANAGER_NAME": source_df["MANAGER_NAME"],

                            "MANAGER_EMAIL": source_df["MANAGER_EMAIL"],

                            "EMPLOYEE_NUMBER": source_df["EMPLOYEE_NUMBER"],

                            "IS_REGIONAL_MANAGER": source_df["IS_REGIONAL_MANAGER"],

                            "CREATEDBY": source_df["CREATEDBY"],

                            "CREATEDDATE": source_df["CREATEDDATE"],

                            "LASTCHANGEDBY": source_df["LASTCHANGEDBY"],

                            "LASTCHANGEDDATE": source_df["LASTCHANGEDDATE"],

                        }

                    ),

                ],

            )

            # change the page and notify the user of the success

        change_page('regional_subs')

        st.success("Updated Successfully")

 

 

def update_subscriptions_audit(sub_info, transaction_user, transaction_type):

 

    last_transaction_id = session.sql("SELECT MAX(TRANSACTION_ID) FROM AUDIT_USLA_REGIONAL_SUBSCRIPTIONS").collect()

    if type(last_transaction_id) is None:

        last_transaction_id = 0

    transaction_id = last_transaction_id[0]["MAX(TRANSACTION_ID)"] + 1

   

    if transaction_type == "Delete":

 

        subscription_id = sub_info[0]["SUBSCRIPTION_ID"]

        service_center_branch_number = sub_info[0]["SERVICE_CENTER_BRANCH_NUMBER"]

        service_center_long_name = sub_info[0]["SERVICE_CENTER_LONG_NAME"]

        manager_name = sub_info[0]["MANAGER_NAME"]

        manager_email = sub_info[0]["MANAGER_EMAIL"]

        employee_number = sub_info[0]["EMPLOYEE_NUMBER"]

        is_regional_manager = sub_info[0]["IS_REGIONAL_MANAGER"]

 

    elif transaction_type == "Create" or transaction_type == "Update":

        subscription_id, service_center_branch_number, service_center_long_name, manager_name, manager_email, employee_number, is_regional_manager = sub_info

   

    source_df = (session.create_dataframe(

        [

            [

                transaction_id,

                subscription_id,

                service_center_branch_number,

                service_center_long_name,

                manager_name,

                manager_email,

                employee_number,

                is_regional_manager,

                transaction_type,

                transaction_user,

            ]

        ],

        schema=["TRANSACTION_ID", "SUBSCRIPTION_ID", "SERVICE_CENTER_BRANCH_NUMBER",

                "SERVICE_CENTER_LONG_NAME", "MANAGER_NAME", "MANAGER_EMAIL",

               "EMPLOYEE_NUMBER", "IS_REGIONAL_MANAGER", "TRANSACTION_TYPE", "TRANSACTION_USER"]

    ).with_column("TRANSACTION_DATE", current_timestamp())

                 .with_column("RECORD_LAST_CHANGED_DATE", current_timestamp()))

 

    target_df = session.table("AUDIT_USLA_REGIONAL_SUBSCRIPTIONS")

    target_df.merge(

        source_df,

        (target_df["TRANSACTION_ID"] == source_df["TRANSACTION_ID"]),

        [

            when_matched().update(

                    {

                        "TRANSACTION_ID": source_df["TRANSACTION_ID"],

                        "SUBSCRIPTION_ID": source_df["SUBSCRIPTION_ID"],

                        "SERVICE_CENTER_BRANCH_NUMBER": source_df["SERVICE_CENTER_BRANCH_NUMBER"],

                        "SERVICE_CENTER_LONG_NAME": source_df["SERVICE_CENTER_LONG_NAME"],

                        "MANAGER_NAME": source_df["MANAGER_NAME"],

                        "MANAGER_EMAIL": source_df["MANAGER_EMAIL"],

                        "EMPLOYEE_NUMBER": source_df["EMPLOYEE_NUMBER"],

                        "IS_REGIONAL_MANAGER": source_df["IS_REGIONAL_MANAGER"],

                        "TRANSACTION_DATE": source_df["TRANSACTION_DATE"],

                        "TRANSACTION_TYPE": source_df["TRANSACTION_TYPE"],

                        "TRANSACTION_USER": source_df["TRANSACTION_USER"],

                        "RECORD_LAST_CHANGED_DATE": source_df["RECORD_LAST_CHANGED_DATE"],

                    }

                ),

                when_not_matched().insert(

                    {

                        "TRANSACTION_ID": source_df["TRANSACTION_ID"],

                        "SUBSCRIPTION_ID": source_df["SUBSCRIPTION_ID"],

                        "SERVICE_CENTER_BRANCH_NUMBER": source_df["SERVICE_CENTER_BRANCH_NUMBER"],

                        "SERVICE_CENTER_LONG_NAME": source_df["SERVICE_CENTER_LONG_NAME"],

                        "MANAGER_NAME": source_df["MANAGER_NAME"],

                        "MANAGER_EMAIL": source_df["MANAGER_EMAIL"],

                        "EMPLOYEE_NUMBER": source_df["EMPLOYEE_NUMBER"],

                        "IS_REGIONAL_MANAGER": source_df["IS_REGIONAL_MANAGER"],

                        "TRANSACTION_DATE": source_df["TRANSACTION_DATE"],

                        "TRANSACTION_TYPE": source_df["TRANSACTION_TYPE"],

                        "TRANSACTION_USER": source_df["TRANSACTION_USER"],

                        "RECORD_LAST_CHANGED_DATE": source_df["RECORD_LAST_CHANGED_DATE"],

                    }

                ),

            ],

        )


 

 

def get_sub_editable(subscription_id):

    session = get_active_session()

    query_subscription = """

        SELECT

            subscription_id,

            service_center_branch_number,

            service_center_long_name,

            manager_name,

            manager_email,

            employee_number,

            is_regional_manager,

        FROM USLA_REGIONAL_SUBSCRIPTIONS scorecard

        WHERE scorecard.subscription_id = subscription_id

    """

    try:

        st.session_state.sub_info = session.sql(query_subscription).to_pandas()

        if len(st.session_state.sub_info) > 0:

            st.session_state.initialized_home = True

        else:

            st.error("0 results returned for subs table")

 

        return st.session_state.sub_info[['SUBSCRIPTION_ID', 'SERVICE_CENTER_BRANCH_NUMBER', 'SERVICE_CENTER_LONG_NAME', 'MANAGER_NAME', 'MANAGER_EMAIL',

                                            'EMPLOYEE_NUMBER', 'IS_REGIONAL_MANAGER']]

 

    except:

        st.error("An Error Occured")

        st.session_state.initialized_home = False

 

# updates the scores for the KPI scorecard based on user input

def update_score_value(session, updates, originals, bound_mode):

    no_errors = True

 

    lastchangedby = get_user_info()

 

    #if 'vuln_error_txt' in st.session_state:

    #    st.error(st.session_state.vuln_error_txt)

    #    no_errors = False

    # error handling: checks for empty text, overlapping bounds

    i = 0

    for i in range (4):

        try:

            curr_min = float(updates[i][1])

            curr_max = float(updates[i][2])

            next_min = float(updates[i + 1][1])

            next_max = float(updates[i + 1][2])

            if bound_mode == "higher":

                if (curr_max < curr_min):

                    st.error("Overlap in score bounds or score dead zone greater than 0.01 detected!")

                    st.error(f'Possible Errored Values: {curr_min}, {curr_max} on score {i + 1}.')

                    no_errors = False

                    break

                elif (round(next_min - curr_max, 2) > 0.01 or next_min < curr_max):

                    st.error("Overlap in score bounds or score dead zone greater than 0.01 detected!")

                    st.error(f'Possible Errored Values: {curr_max}, {next_min} on scores {i + 1} and {i + 2}.')

                    no_errors = False

                    break

                elif (next_max < next_min):

                    st.error("Overlap in score bounds or score dead zone greater than 0.01 detected!")

                    st.error(f'Possible Errored Values: {next_min}, {next_max} on score {i + 2}.')

                    no_errors = False

                    break

 

            elif bound_mode == "lower":

                if (curr_max < curr_min):

                    st.error("Overlap in score bounds or score dead zone greater than 0.01 detected!")

                    st.error(f'Possible Errored Values: {curr_min}, {curr_max} on score {i + 1}.')

                    no_errors = False

                    break

 

                elif (round(curr_min - next_max, 2) > 0.01) or curr_min > next_max:

                    st.error("Overlap in score bounds or score dead zone greater than 0.01 detected!")

                    st.error(f'Possible Errored Values: {curr_min}, {next_max} on scores {i + 1} and {i + 2}.')

                    no_errors = False

                    break

 

                elif (next_max < next_min):

                    st.error("Overlap in score bounds or score dead zone greater than 0.01 detected!")

                    st.error(f'Possible Errored Values: {next_min}, {next_max} on score {i + 2}.')

                    no_errors = False

                    break

        except:

            st.error("All inputs must be numeric!")

            no_errors = False

            break

 

    if no_errors:

        no_updates = True

 

        j = 0

        for j in range(5):

            if (updates[j][1] != originals[0][j]) or (updates[j][2] != originals[1][j]):

                category_id, min_value, max_value, score = updates[j]

                no_updates = False

                score_info = (min_value, max_value, score)

                update_matrix_audit(category_id, score_info, lastchangedby, "Update")

   

                source_df = (session.create_dataframe(

                    [

                        [

                            category_id,

                            min_value,

                            max_value,

                            score,

                            lastchangedby,

                        ]

                    ],

                    schema=["CATEGORY_ID", "MIN_VALUE", "MAX_VALUE", "SCORE",

                            "LASTCHANGEDBY"],

       

                ).with_column("LASTCHANGEDDATE", current_timestamp()))

       

                target_df = session.table("USLA_SCORECARD_MATRIX")

       

                target_df.merge(

                    source_df,

                    ((target_df["CATEGORY_ID"] == source_df["CATEGORY_ID"])

                     & (target_df["SCORE"] == source_df["SCORE"])),

                    [

                        when_matched().update(

                            {

                                "MIN_VALUE": source_df["MIN_VALUE"],

                                "MAX_VALUE": source_df["MAX_VALUE"],

                                "LASTCHANGEDBY": source_df["LASTCHANGEDBY"],

                                "LASTCHANGEDDATE": source_df["LASTCHANGEDDATE"],

                            }

                        ),

                        when_not_matched().insert(

                            {

                                "MIN_VALUE": source_df["MIN_VALUE"],

                                "MAX_VALUE": source_df["MAX_VALUE"],

                                "LASTCHANGEDBY": source_df["LASTCHANGEDBY"],

                                "LASTCHANGEDDATE": source_df["LASTCHANGEDDATE"],

                            }

                        ),

                    ],

                )

            # change the page and notify the user of the success

        if not no_updates:

            change_page('kpi_matrix')

            st.success("Updated Successfully")

        else:

            st.error("No changes made!")

 

 

def update_matrix_audit(category_id, score_info, transaction_user, transaction_type):

 

    last_transaction_id = session.sql("SELECT MAX(TRANSACTION_ID) FROM AUDIT_USLA_SCORECARD_MATRIX").collect()

    if type(last_transaction_id) is None:

        last_transaction_id = 0

    transaction_id = last_transaction_id[0]["MAX(TRANSACTION_ID)"] + 1

 

    matrix_id = category_id

 

    min_value, max_value, score = score_info

   

    source_df = (session.create_dataframe(

        [

            [

                transaction_id,

                matrix_id,

                category_id,

                min_value,

                max_value,

                score,

                transaction_type,

                transaction_user,

            ]

        ],

        schema=["TRANSACTION_ID", "MATRIX_ID", "CATEGORY_ID", "MIN_VALUE", "MAX_VALUE",

               "SCORE", "TRANSACTION_TYPE", "TRANSACTION_USER"]

    ).with_column("TRANSACTION_DATE", current_timestamp())

                 .with_column("RECORD_LAST_CHANGED_DATE", current_timestamp()))

 

    target_df = session.table("AUDIT_USLA_SCORECARD_MATRIX")

    target_df.merge(

        source_df,

        (target_df["TRANSACTION_ID"] == source_df["TRANSACTION_ID"]),

        [

            when_matched().update(

                    {

                        "TRANSACTION_ID": source_df["TRANSACTION_ID"],

                        "MATRIX_ID" : source_df["MATRIX_ID"],

                        "CATEGORY_ID": source_df["CATEGORY_ID"],

                        "MIN_VALUE": source_df["MIN_VALUE"],

                        "MAX_VALUE": source_df["MAX_VALUE"],

                        "SCORE": source_df["SCORE"],

                        "TRANSACTION_DATE": source_df["TRANSACTION_DATE"],

                        "TRANSACTION_TYPE": source_df["TRANSACTION_TYPE"],

                        "TRANSACTION_USER": source_df["TRANSACTION_USER"],

                        "RECORD_LAST_CHANGED_DATE": source_df["RECORD_LAST_CHANGED_DATE"],

                    }

                ),

                when_not_matched().insert(

                    {

                        "TRANSACTION_ID": source_df["TRANSACTION_ID"],

                        "MATRIX_ID" : source_df["MATRIX_ID"],

                        "CATEGORY_ID": source_df["CATEGORY_ID"],

                        "MIN_VALUE": source_df["MIN_VALUE"],

                        "MAX_VALUE": source_df["MAX_VALUE"],

                        "SCORE": source_df["SCORE"],

                        "TRANSACTION_DATE": source_df["TRANSACTION_DATE"],

                        "TRANSACTION_TYPE": source_df["TRANSACTION_TYPE"],

                        "TRANSACTION_USER": source_df["TRANSACTION_USER"],

                        "RECORD_LAST_CHANGED_DATE": source_df["RECORD_LAST_CHANGED_DATE"],

                    }

                ),

            ],

        )


 

# updates the KPI category weights based on user input

def update_weight_value(session, weight_array, originals):

    no_errors = True

 

    lastchangedby = get_user_info()

 

    #error handling: checks for negative/empty entries, and that all

    #scores total 100.

    total = 0

    for id, weight in weight_array:

        try:

            weight = float(weight)

        except:

            st.error("All weights must be numeric!")

            no_errors = False

            break

           

        if weight < 0:

            st.error("Weights cannot be negative!")

            no_errors = False

 

        total += weight

 

    if total != 100:

        st.error("Weights must add up to 100!")

        no_errors = False

 

    # if no errors, proceed to update the database based on user input

    if no_errors:

        k = 0

        no_updates = True

        for k in range(10):

            category_id, weight = weight_array[k]

            if weight != originals[k]:

                no_updates = False

                update_weight_audit(k + 1, weight, lastchangedby, "Update")

       

                source_df = (session.create_dataframe(

                    [

                        [

                            category_id,

                            weight,

                            lastchangedby,

                        ]

                    ],

                    schema=["CATEGORY_ID", "WEIGHT", "LASTCHANGEDBY"

                            ],

       

                ).with_column("LASTCHANGEDDATE", current_timestamp()))

       

                target_df = session.table("USLA_SCORECARD_CATEGORY")

       

                target_df.merge(

                    source_df,

                    (target_df["CATEGORY_ID"] == source_df["CATEGORY_ID"]),

                     ## & (target_df["WEIGHT"] == source_df["WEIGHT"])),

                    [

                        when_matched().update(

                            {

                                "WEIGHT": source_df["WEIGHT"],

                                "LASTCHANGEDBY": source_df["LASTCHANGEDBY"],

                                "LASTCHANGEDDATE": source_df["LASTCHANGEDDATE"],

                            }

                        ),

                        when_not_matched().insert(

                            {

                                "WEIGHT": source_df["WEIGHT"],

                                ##"LASTCHANGEDBY": source_df["LASTCHANGEDBY"],

                                ##"LASTCHANGEDDATE": source_df["LASTCHANGEDDATE"],

                            }

                        ),

                    ],

                )

        # change page and notify the user if successful changes made

        if not no_updates:

            change_page('kpi_matrix')

            st.success("Updated Successfully")

        else:

            st.error("No changes made!")

 

def update_weight_audit(category_id, weight, transaction_user, transaction_type):

 

    last_transaction_id = session.sql("SELECT MAX(TRANSACTION_ID) FROM AUDIT_USLA_SCORECARD_CATEGORY").collect()

    if type(last_transaction_id) is None:

        last_transaction_id = 0

    transaction_id = last_transaction_id[0]["MAX(TRANSACTION_ID)"] + 1


    source_df = (session.create_dataframe(

        [

            [

                transaction_id,

                category_id,

                weight,

                transaction_type,

                transaction_user,

            ]

        ],

        schema=["TRANSACTION_ID", "CATEGORY_ID", "WEIGHT",

               "TRANSACTION_TYPE", "TRANSACTION_USER"]

    ).with_column("TRANSACTION_DATE", current_timestamp())

                 .with_column("RECORD_LAST_CHANGED_DATE", current_timestamp()))

 

    target_df = session.table("AUDIT_USLA_SCORECARD_CATEGORY")

    target_df.merge(

        source_df,

        (target_df["TRANSACTION_ID"] == source_df["TRANSACTION_ID"]),

        [

            when_matched().update(

                    {

                        "TRANSACTION_ID": source_df["TRANSACTION_ID"],

                        "CATEGORY_ID": source_df["CATEGORY_ID"],

                        "WEIGHT": source_df["WEIGHT"],

                        "TRANSACTION_DATE": source_df["TRANSACTION_DATE"],

                        "TRANSACTION_TYPE": source_df["TRANSACTION_TYPE"],

                        "TRANSACTION_USER": source_df["TRANSACTION_USER"],

                        "RECORD_LAST_CHANGED_DATE": source_df["RECORD_LAST_CHANGED_DATE"],

                    }

                ),

                when_not_matched().insert(

                    {

                        "TRANSACTION_ID": source_df["TRANSACTION_ID"],

                        "CATEGORY_ID": source_df["CATEGORY_ID"],

                        "WEIGHT": source_df["WEIGHT"],

                        "TRANSACTION_DATE": source_df["TRANSACTION_DATE"],

                        "TRANSACTION_TYPE": source_df["TRANSACTION_TYPE"],

                        "TRANSACTION_USER": source_df["TRANSACTION_USER"],

                        "RECORD_LAST_CHANGED_DATE": source_df["RECORD_LAST_CHANGED_DATE"],

                    }

                ),

            ],

        )


# gets subscriptions matrix

def get_subs():

    session = get_active_session()

    subs = """

        SELECT

            subscription_id,

            service_center_long_name,

            manager_name,

            manager_email,

            employee_number,

            is_regional_manager

        FROM USLA_REGIONAL_SUBSCRIPTIONS subs

        ORDER BY createddate desc

        """

 

    try:

        st.session_state.subs_info = session.sql(subs).to_pandas()

       

        if len(st.session_state.subs_info) > 0:

            st.session_state.initialized_home = True

        else:

            st.error("0 results returned for subs table")

 

        return st.session_state.subs_info[['SUBSCRIPTION_ID', 'SERVICE_CENTER_LONG_NAME'

                                               , 'MANAGER_NAME', 'MANAGER_EMAIL', 'EMPLOYEE_NUMBER', 'IS_REGIONAL_MANAGER']]

 

    except:

        st.error("An Error Occured")

        st.session_state.initialized_home = False

 

 

def get_subs_audit():

    session = get_active_session()

    subs_audit = """

        SELECT

            transaction_id,

            subscription_id,

            service_center_long_name,

            manager_name,

            manager_email,

            employee_number,

            is_regional_manager,

            transaction_date,

            transaction_type,

            transaction_user,

        FROM AUDIT_USLA_REGIONAL_SUBSCRIPTIONS subs

        """

 

    try:

        st.session_state.subs_audit_info = session.sql(subs_audit).to_pandas()       

        

        if len(st.session_state.subs_audit_info) > 0:

            st.session_state.initialized_home = True

        else:

            st.error("0 results returned for subs table")

 

        return st.session_state.subs_audit_info[['TRANSACTION_ID', 'SUBSCRIPTION_ID', 'SERVICE_CENTER_LONG_NAME'

                                               , 'MANAGER_NAME', 'MANAGER_EMAIL', 'EMPLOYEE_NUMBER', 'IS_REGIONAL_MANAGER',

                                           'TRANSACTION_DATE', 'TRANSACTION_TYPE', 'TRANSACTION_USER']]

 

    except:

        st.error("An Error Occured")

        st.session_state.initialized_home = False

 

 

# gets scorecard category matrix

def get_score_cat():

    session = get_active_session()

    query_categories = """

        SELECT

            category_id,

            category,

            weight,

            createdby,

            createddate,

            lastchangedby,

            lastchangeddate,

        FROM USLA_SCORECARD_CATEGORY scorecard

        """

 

    try:

        st.session_state.kpi_info = session.sql(query_categories).to_pandas()

 

        if len(st.session_state.kpi_info) > 0:

            st.session_state.initialized_home = True

        else:

            st.error("0 results returned for subs table")

 

        return st.session_state.kpi_info[['CATEGORY_ID', 'CATEGORY', 'WEIGHT', 'CREATEDBY',

                                            'CREATEDDATE', 'LASTCHANGEDBY', 'LASTCHANGEDDATE']]

 

    except:

        st.error("An Error Occured")

        st.session_state.initialized_home = False

 

def get_score_cat_audit():

    session = get_active_session()

 

    query_audit = """

        SELECT

            transaction_id,

            category_id,

            weight,

            transaction_date,

            transaction_type,

            transaction_user,

        FROM AUDIT_USLA_SCORECARD_CATEGORY audit

    """

    try:

        st.session_state.audit_info = session.sql(query_audit).to_pandas()

        if len(st.session_state.audit_info) > 0:

            st.session_state.initialized_home = True

        else:

            st.error("0 results returned for audit log")

 

        return st.session_state.audit_info[['TRANSACTION_ID', 'CATEGORY_ID', 'WEIGHT',

                                       'TRANSACTION_DATE', 'TRANSACTION_TYPE', 'TRANSACTION_USER']]

 

    except:

        st.error("An Error Occured")

        st.session_state.initialized_home = False

 

# gets KPI scores matrix

def get_score_matrix():

    session = get_active_session()

    query_matrix = """

        SELECT

            category_id,

            min_value,

            max_value,

            score

        FROM USLA_SCORECARD_MATRIX matrix

        """

    try:

        st.session_state.matrix_info = session.sql(query_matrix).to_pandas()

   

        if len(st.session_state.matrix_info) > 0:

            st.session_state.initialized_home = True

        else:

            st.error("0 results returned for matrix table")

   

        return st.session_state.matrix_info[['CATEGORY_ID', 'MIN_VALUE', 'MAX_VALUE', 'SCORE']]

 

    except:

        st.error("An Error Occured")

        st.session_state.initialized_home = False

 

def get_score_matrix_audit():

    session = get_active_session()

    query_matrix_audit = """

        SELECT

            transaction_id,

            matrix_id,

            category_id,

            min_value,

            max_value,

            score,

            transaction_date,

            transaction_type,

            transaction_user,

        FROM AUDIT_USLA_SCORECARD_MATRIX matrix

        """

    try:

        st.session_state.matrix_audit_info = session.sql(query_matrix_audit).to_pandas()

   

        if len(st.session_state.matrix_audit_info) > 0:

            st.session_state.initialized_home = True

        else:

            st.error("0 results returned for matrix table")

   

        return st.session_state.matrix_audit_info[['TRANSACTION_ID', 'MATRIX_ID', 'CATEGORY_ID', 'MIN_VALUE',

                                            'MAX_VALUE', 'SCORE', 'TRANSACTION_DATE',

                                           'TRANSACTION_TYPE', 'TRANSACTION_USER']]

 

    except:

        st.error("An Error Occured")

        st.session_state.initialized_home = False

 

 

# creates matrixes given a category id from a particular matrix

def create_matrix(df_matrix, category_id):

        st.write("")

        cols = st.columns(4)

        fields = ['Category ID', 'Minimum Value', 'Maximum Value', 'Score']

 

        for column, field in zip(cols, fields):

            column.write("**" + field + "**")

 

        filtered_df = df_matrix[df_matrix["CATEGORY_ID"] == category_id]

       

        for idx, row in filtered_df.iterrows():

            col1, col2, col3, col4 = st.columns(4)

            with col1:

                st.write(str(row["CATEGORY_ID"]))

            with col2:

                st.write(str(row["MIN_VALUE"]))

            with col3:

                st.write(str(row["MAX_VALUE"]))

            with col4:

                st.write(str(row["SCORE"]))

   

 

 

# sidebar for tabs/buttons to tabs

new_sidebar = st.sidebar

 

with st.sidebar:

    dataimage = Image.open("crawford.png")

    st.image(dataimage, width=250)

    st.header('USLA Reference Data Application', divider='blue')

    if st.button('Regional Subscriptions', help="Navigate to the regional subscriptions page.", key="regional_subs"):

        change_page('regional_subs')

    if st.button('KPI Adjuster Matrix', help="Navigate to the KPI Adjuster Matrix page.", key="adjuster_matrix"):

        change_page('kpi_matrix')

    if st.button('Audit Log', help="Navigate to the Audit Log page.", key="audit_log"):

        change_page('audit_log')

 

# functionality for buttons on the sidebar, setting up pages

 

#############################################################

#

# logic for the regional subs page

#

#############################################################

if st.session_state['current_page'] == 'regional_subs':

    # header and add button for regional subscriptions

    st.header('USLA Regional Subscriptions', divider='blue')

 

    df = get_subs()

 

    #########

    # Filters for reg subs page

    #########

   

    st.caption("Filter Subscriptions")

 

    service_center_options = sorted(df['SERVICE_CENTER_LONG_NAME'].unique().tolist())

    manager_options = sorted(df['MANAGER_NAME'].unique().tolist())

    employee_number_options = sorted(df['EMPLOYEE_NUMBER'].unique().tolist())

    regional_manager_status = sorted(df['IS_REGIONAL_MANAGER'].unique().tolist())

 

    col1, col2, col3, col4 = st.columns((2, 1.5, 1, 1))

 

    with col1:

        st.session_state.service_center_filter = st.multiselect('Service Center', service_center_options)

    with col2:

        st.session_state.manager_filter = st.multiselect('Manager Name', manager_options)

    row2_col1, row2_col2, row2_col3, row2_col4 = st.columns((2, 1.5, 1, 1))

 

    with row2_col1:

        st.session_state.employee_number_filter = st.multiselect('Employee Number', employee_number_options)

    with row2_col2:

        st.session_state.regional_manager_filter = st.multiselect('Regional Manager Status', regional_manager_status)

    with row2_col3:

        st.header("")

    with row2_col4:

        st.header("")

 

    st.caption("Add a new Subscription")

    st.button('Add Subscription', help='Add a regional subscription', key="add_sub", on_click=change_page, args=('add_sub',))

 

    #apply filters

    if st.session_state.service_center_filter:

        df = df[df["SERVICE_CENTER_LONG_NAME"].isin(st.session_state.service_center_filter)]

    if st.session_state.manager_filter:

        df = df[df["MANAGER_NAME"].isin(st.session_state.manager_filter)]

    if (st.session_state.employee_number_filter):

        df = df[df["EMPLOYEE_NUMBER"].isin(st.session_state.employee_number_filter)]

    if st.session_state.regional_manager_filter:

        df = df[df["IS_REGIONAL_MANAGER"].isin(st.session_state.regional_manager_filter)]

   

    df_summary = df[['SUBSCRIPTION_ID', 'SERVICE_CENTER_LONG_NAME',

                    'MANAGER_NAME', 'MANAGER_EMAIL', 'EMPLOYEE_NUMBER', 'IS_REGIONAL_MANAGER']]

   

    #gets the suscriptions matrix and sets it up in a container

 

    pagination = st.container()

 

    bottom_menu = st.columns((4, 1, 1))

    with bottom_menu[2]:

        batch_size = st.selectbox("Page Size", options=[5, 10, 25, 75, 100])

    with bottom_menu[1]:

        total_pages = (

            int(math.ceil(len(df_summary) / batch_size)) if int(len(df_summary) / batch_size) > 0 else 1

        )

        current_page = st.number_input(

            "Page", min_value=1, max_value=total_pages, step=1

        )

    with bottom_menu[0]:

        st.markdown(f"Page **{current_page}** of **{total_pages}** ")

   

    pages = split_frame(df_summary, batch_size)

   

    if current_page >= 1 and len(df_summary) > 0:

        current_df = pages[current_page - 1]

    else:

        current_df = df

 

    # if any filters applied, then display original df on results

    if (st.session_state.service_center_filter

            or st.session_state.manager_filter or st.session_state.employee_number_filter

            or st.session_state.regional_manager_filter):

        current_df = df

 

    with pagination:

        st.write("")

        cols = st.columns((1, 1.5, 1, 1.5, 1, 1, .75, .75))

        fields = ['Subscription Id', 'Service Center', 'Manager Name', 'Manager Email', 'Employee Number', 'Regional Manager Status', 'Actions']

   

        for column, field in zip(cols, fields):

            column .write("**" + field + "**")

 

        if current_df.empty:

            st.warning("No subscriptions match the applied filters.")

       

        for idx, row in current_df.iterrows():

            col0, col1, col2, col3, col4, col5, col6, col7 = st.columns((1, 1.5, 1, 1.5, 1, 1, .75, .75))

            with col0:

                st.write(row["SUBSCRIPTION_ID"])

            with col1:

                st.write(row["SERVICE_CENTER_LONG_NAME"])

            with col2:

                st.write(row["MANAGER_NAME"])

            with col3:

                st.write(row["MANAGER_EMAIL"])

            with col4:

                st.write(str(row["EMPLOYEE_NUMBER"]))

            with col5:

                st.write(str(row["IS_REGIONAL_MANAGER"]))

            with col6:

                st.button(label=":gear:", help="Edit Subscription ID " + str(row["SUBSCRIPTION_ID"]),

                                          key="edit" + str(idx),

                                          on_click=change_page,

                                          args=('edit_sub', row["SUBSCRIPTION_ID"]))

            with col7:

                st.button(label=":x:", help="Delete Subscription ID " + str(row["SUBSCRIPTION_ID"]),

                    key="delete" + str(idx),

                    on_click=delete_sub,

                    args=(row["SUBSCRIPTION_ID"],))

               

            if 'delete_subscription_id' in st.session_state:

                if st.session_state.delete_subscription_id == row["SUBSCRIPTION_ID"]:

                    col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns(

                        (.5, 1.5, 1, 1, 1, 1, 1, 1, 1))

                    with col9:

                        st.write("Confirm Delete?")

                   

                    # This is the confirm delete on delete button click

                    col1_sub, col2_sub, col3_sub, col4_sub, col5_sub, col6_sub, col7_sub, col8_sub, col9_sub, col10_sub = st.columns(

                        (.5, 1.5, 1, 1, 1, 1, 1, 1, .5, .5))

                    with col9_sub:

                        st.button(label="Yes", key="Yes", on_click=delete_confirm,

                                args=(1, row["SUBSCRIPTION_ID"]))

                    with col10_sub:

                        st.button(label="No", key="No", on_click=delete_confirm, args=(0,))

 

 

#############################################################

#

# logic for the KPI adjuster matrix page

#

#############################################################

 

elif st.session_state['current_page'] == 'kpi_matrix':

    # header for the matrix scorecard

    st.header('USLA KPI Adjuster Matrix', divider='blue')

 

    # get general matrix info for calc

    df_overview = get_score_cat()

    df_matrix = get_score_matrix()

 

    # button for editing each weight  

    st.button('Edit Weights', help="Configure", on_click=change_page, args=("edit_weights",))

 

 

    # create the tabs for individual KPIs

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11 = st.tabs(["Overview", "Production Dollars",

                "First Contact", "First Visit", "First Visit to Estimate", "First Report", "Estimate Return",

                "TIP Compliance", "Diary Compliance", "Quality Review", "PSR Audit"])

 

    # setting so each database only appears on one tab, with a brief description

    with tab1:

        pagination = st.container()

 

        with pagination:

            st.write("")

            cols = st.columns((1.5, 2, 1.5, 1.5, 1.5, 1.5, 1.5))

            fields = ['Category ID', 'Category', 'Weight', 'Created By', 'Created Date', 'Last Changed By', 'Last Changed Date']

       

            for column, field in zip(cols, fields):

                column .write("**" + field + "**")

       

            for idx, row in df_overview.iterrows():

                col1, col2, col3, col4, col5, col6, col7 = st.columns((1.5, 2, 1.5, 1.5, 1.5, 1.5, 1.5))

                with col1:

                    st.write(str(row["CATEGORY_ID"]))

                with col2:

                    st.write(row["CATEGORY"])

                with col3:

                    st.write(str(row["WEIGHT"]))

                with col4:

                    st.write(row["CREATEDBY"])

                with col5:

                    st.write(row["CREATEDDATE"])

                with col6:

                    st.write(row["LASTCHANGEDBY"])

                with col7:

                    st.write(row["LASTCHANGEDDATE"])

 

   

    with tab2:

        st.caption("This metric evaluates the total dollar amount of production " +

                   "achieved within a specified period. It reflects the financial " +

                   "output or revenue generated by the operations being monitored.")

        create_matrix(df_matrix, 1)

        st.button(label="Edit table", help="Edit table",

                                  key="edit_matrix1",

                                  on_click=change_page_and_val, args=("edit_matrix", 1))

   

    with tab3:

        st.caption("The number of days from initial receipt of a request or task " +

                   "until the first contact or communication is established with the " +

                   "relevant parties. A higher score signifies prompt responsiveness.")

        create_matrix(df_matrix, 2)

        st.button(label="Edit table", help="Edit table",

                                  key="edit_matrix2",

                                  on_click=change_page_and_val, args=("edit_matrix", 2))

   

    with tab4:

        st.caption("Measures the elapsed time from receiving a request until the " +

                   "first physical visit or inspection occurs. A higher score " +

                   "indicates efficient scheduling and execution of site visits.")   

        create_matrix(df_matrix, 3)

        st.button(label="Edit table", help="Edit table",

                                  key="edit_matrix3",

                                  on_click=change_page_and_val, args=("edit_matrix", 3))

   

    with tab5:

        st.caption("This metric tracks the duration from the moment a request or " +

                   "task is received until the estimate or proposal detailing the " +

                   "cost, scope, and timeline is completed and delivered to the requesting party.")

        create_matrix(df_matrix, 4)

        st.button(label="Edit table", help="Edit table",

                                  key="edit_matrix4",

                                  on_click=change_page_and_val, args=("edit_matrix", 4))

   

    with tab6:

        st.caption("This category assesses the time taken from receiving a request " +

                   "until the first formal report or documentation is submitted. A " +

                   "shorter time frame indicates expedient reporting and communication.")   

        create_matrix(df_matrix, 5)

        st.button(label="Edit table", help="Edit table",

                                  key="edit_matrix5",

                                  on_click=change_page_and_val, args=("edit_matrix", 5))

   

    with tab7:

        st.caption("Tracks the duration from the initial site visit or inspection " +

                   "to the completion and delivery of the cost estimation or project " +

                   "proposal. A shorter duration implies swift processing and assessment.")   

        create_matrix(df_matrix, 6)

        st.button(label="Edit table", help="Edit table",

                                  key="edit_matrix6",

                                  on_click=change_page_and_val, args=("edit_matrix", 6))

   

    with tab8:

        st.caption("Refers to adherence to the Treatment Improvement Protocols (TIPs) " +

                   "set forth by regulatory or organizational guidelines. A higher score " +

                   "indicates better compliance with these standards.")   

        create_matrix(df_matrix, 7)

        st.button(label="Edit table", help="Edit table",

                                  key="edit_matrix7",

                                  on_click=change_page_and_val, args=("edit_matrix", 7))

   

    with tab9:

        st.caption("Measures compliance with diary or journaling requirements, " +

                   "where events, actions, or milestones must be recorded " +

                   "systematically. A higher score indicates better adherence " +

                   "to these recording practices.")   

        create_matrix(df_matrix, 8)

        st.button(label="Edit table", help="Edit table",

                                  key="edit_matrix8",

                                  on_click=change_page_and_val, args=("edit_matrix", 8))

   

    with tab10:

        st.caption("This category measures the accuracy and completeness of the " +

                   "review process for both quality assurance and billing activities. " +

                   "A higher score indicates thoroughness and attention to detail in " +

                   "these critical processes.")   

        create_matrix(df_matrix, 9)

        st.button(label="Edit table", help="Edit table",

                                  key="edit_matrix9",

                                  on_click=change_page_and_val, args=("edit_matrix", 9))

   

    with tab11:

        st.caption("Stands for Performance and Service Review audit, " +

                   "evaluating overall performance against predefined " +

                   "service metrics and benchmarks. A higher score reflects strong " +

                   "performance and adherence to service standards.")

        create_matrix(df_matrix, 10)

        st.button(label="Edit table", help="Edit table",

                                  key="edit_matrix10",

                                  on_click=change_page_and_val, args=("edit_matrix", 10))

 

 

#############################################################

#

# logic for the audit log page

#

#############################################################

 

elif st.session_state['current_page'] == 'audit_log':

    st.header('Audit Logs', divider='blue')

   

    reg_sub_audit, score_cat_audit, score_matrix_audit = st.tabs([

        "Regional Subscriptions", "Scorecard Category", "Scorecard Matrix"])

 

    with reg_sub_audit:

        df_overview = get_subs_audit()

 

        # Filter selector for reg sub audit log

        sub_id_options = sorted(df_overview['SUBSCRIPTION_ID'].unique().tolist())

        st.session_state.sub_id_filter = st.multiselect('Filter by Subscription ID', sub_id_options)

 

        if st.session_state.sub_id_filter:

            df_overview = df_overview[df_overview['SUBSCRIPTION_ID'].isin(st.session_state.sub_id_filter)]

       

        df_summary = df_overview[['TRANSACTION_ID', 'SUBSCRIPTION_ID', 'SERVICE_CENTER_LONG_NAME',

                      'MANAGER_NAME', 'MANAGER_EMAIL', 'EMPLOYEE_NUMBER', 'IS_REGIONAL_MANAGER',

                      'TRANSACTION_DATE', 'TRANSACTION_TYPE', 'TRANSACTION_USER']]

       

        pagination1 = st.container()

 

        bottom_menu = st.columns((4, 1, 1))

        with bottom_menu[2]:

            batch_size = st.selectbox(label="Page Size", key=1, options=[5, 10, 25, 75, 100])

        with bottom_menu[1]:

            total_pages = (

                int(math.ceil(len(df_summary) / batch_size)) if int(len(df_summary) / batch_size) > 0 else 1

            )

            current_page = st.number_input(

                "Page", min_value=1, max_value=total_pages, step=1

            )

        with bottom_menu[0]:

            st.markdown(f"Page **{current_page}** of **{total_pages}** ")

       

        pages = split_frame(df_summary, batch_size)

       

        if current_page >= 1 and len(df_summary) > 0:

            current_df = pages[current_page - 1]

        else:

            current_df = df_summary

 

        with pagination1:

            st.write("")

            cols = st.columns(10)

            fields = ['Transaction Id', 'Subscription ID', 'Service Center',

                      'Manager Name', 'Manager Email', 'Employee Number', 'Regional Manager Status',

                      'Transaction Date', 'Transaction Type', 'Transaction User']

           

            for column, field in zip(cols, fields):

                column .write("**" + field + "**")

       

            for idx, row in current_df.iterrows():

                col1, col2, col3, col4, col5, col6, col7, col8, col9, col10= st.columns(10)

                with col1:

                    st.write(str(row["TRANSACTION_ID"]))

                with col2:

                    st.write(str(row["SUBSCRIPTION_ID"]))

                with col3:

                    st.write(row["SERVICE_CENTER_LONG_NAME"])

                with col4:

                    st.write(row["MANAGER_NAME"])

                with col5:

                    st.write(row["MANAGER_EMAIL"])

                with col6:

                    st.write(str(row["EMPLOYEE_NUMBER"]))

                with col7:

                    st.write(str(row["IS_REGIONAL_MANAGER"]))

                with col8:

                    st.write(str(row["TRANSACTION_DATE"]))

                with col9:

                    st.write(row["TRANSACTION_TYPE"])

                with col10:

                    st.write(row["TRANSACTION_USER"])

 

    ## Tab for the scorecard category audit table

    with score_cat_audit:

        df_overview = get_score_cat_audit()

 

        # Filter selector for scorecard category audit log

        cat_id_options = sorted(df_overview['CATEGORY_ID'].unique().tolist())

        st.session_state.cat_id_filter = st.multiselect('Filter by Category ID', cat_id_options)

 

        if st.session_state.cat_id_filter:

            df_overview = df_overview[df_overview['CATEGORY_ID'].isin(st.session_state.cat_id_filter)]

       

        df_summary = df_overview[['TRANSACTION_ID', 'CATEGORY_ID',  'WEIGHT', 'TRANSACTION_DATE',

                      'TRANSACTION_TYPE', 'TRANSACTION_USER']]

       

        pagination2 = st.container()

 

        bottom_menu = st.columns((4, 1, 1))

        with bottom_menu[2]:

            batch_size = st.selectbox(label="Page Size", key=2, options=[5, 10, 25, 75, 100])

        with bottom_menu[1]:

            total_pages = (

                int(math.ceil(len(df_summary) / batch_size)) if int(len(df_summary) / batch_size) > 0 else 1

            )

            current_page = st.number_input(

                "Page", key="number_input2", min_value=1, max_value=total_pages, step=1

            )

        with bottom_menu[0]:

            st.markdown(f"Page **{current_page}** of **{total_pages}** ")

       

        pages = split_frame(df_summary, batch_size)

       

        if current_page >= 1 and len(df_summary) > 0:

            current_df = pages[current_page - 1]

        else:

            current_df = df_summary

 

        with pagination2:

            st.write("")

            cols = st.columns(6)

            fields = ['Transaction ID', 'Category ID', 'Weight', 'Transaction Date', 'Transaction Type', 'Transaction User']

 

            for column, field in zip(cols, fields):

                column.write("**" + field + "**")

 

            for idx, row in current_df.iterrows():

                col1, col2, col3, col4, col5, col6 = st.columns(6)

                with col1:

                    st.write(str(row["TRANSACTION_ID"]))

                with col2: 

                    st.write(str(row["CATEGORY_ID"]))

                with col3:

                    st.write(str(row["WEIGHT"]))

                with col4:

                    st.write(str(row["TRANSACTION_DATE"]))

                with col5:

                    st.write(str(row["TRANSACTION_TYPE"]))

                with col6:

                    st.write(str(row["TRANSACTION_USER"]))

 

    with score_matrix_audit:

        #####CHANGE TO PROPER TABLE INFO, THIS ACTS AS EXAMPLE#####

        df_overview = get_score_matrix_audit()

 

        # Filter selector for scorecard category audit log

        cat_id_options = sorted(df_overview['CATEGORY_ID'].unique().tolist())

        st.session_state.cat_id_filter = st.multiselect('Filter by Category ID', cat_id_options)

 

        if st.session_state.cat_id_filter:

            df_overview = df_overview[df_overview['CATEGORY_ID'].isin(st.session_state.cat_id_filter)]

       

        df_summary = df_overview[['TRANSACTION_ID', 'CATEGORY_ID',  'MIN_VALUE', 'MAX_VALUE', 'SCORE',

                                  'TRANSACTION_DATE', 'TRANSACTION_TYPE', 'TRANSACTION_USER']]

       

        pagination3 = st.container()

 

        bottom_menu = st.columns((4, 1, 1))

        with bottom_menu[2]:

            batch_size = st.selectbox(label="Page Size", key=3, options=[5, 10, 25, 75, 100])

        with bottom_menu[1]:

            total_pages = (

                int(math.ceil(len(df_overview) / batch_size)) if int(len(df_overview) / batch_size) > 0 else 1

            )

            current_page = st.number_input(

                "Page", key="number_input3", min_value=1, max_value=total_pages, step=1

            )

        with bottom_menu[0]:

            st.markdown(f"Page **{current_page}** of **{total_pages}** ")

       

        pages = split_frame(df_overview, batch_size)

       

        if current_page >= 1 and len(df_overview) > 0:

            current_df = pages[current_page - 1]

        else:

            current_df = df_overview

 

       

        with pagination3:

            st.write("")

            cols = st.columns(8)

            fields = ['Transaction Id', 'Category ID', 'Minimum Value',

                      'Maximum Value', 'Score', 'Transaction Date', 'Transaction Type',

                      'Transaction User']

           

            for column, field in zip(cols, fields):

                column .write("**" + field + "**")

       

            for idx, row in df_overview.iterrows():

                col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)

                with col1:

                    st.write(str(row["TRANSACTION_ID"]))

                with col2:

                    st.write(str(row["CATEGORY_ID"]))

                with col3:

                    st.write(str(row["MIN_VALUE"]))

                with col4:

                    st.write(str(row["MAX_VALUE"]))

                with col5:

                    st.write(str(row["SCORE"]))

                with col6:

                    st.write(str(row["TRANSACTION_DATE"]))

                with col7:

                    st.write(row["TRANSACTION_TYPE"])

                with col8:

                    st.write(row["TRANSACTION_USER"])

 

 

#############################################################

#

# logic for the edit KPI matrix pages

#

#############################################################

elif st.session_state['current_page'] == 'edit_matrix':

   

    # fetch the main dataframe

    df_matrix = get_score_matrix()

    key_matrix_category = st.session_state['key_category_id']

 

    header_spec = ""

    bound_mode = ""

 

    # gets identities for each matrix, customizes the page based on key

    # also sets bounds for error handling

    if key_matrix_category == 1:

        header_spec = "Production Dollars"

        bound_mode = "higher"

    elif key_matrix_category == 2:

        header_spec = "First Contact"

        bound_mode = "lower"

    elif key_matrix_category == 3:

        header_spec = "First Visit"

        bound_mode = "lower"

    elif key_matrix_category == 4:

        header_spec = "First Visit to Estimate"

        bound_mode = "lower"

    elif key_matrix_category == 5:

        header_spec = "First Report"

        bound_mode = "lower"

    elif key_matrix_category == 6:

        header_spec = "Estimate Return"

        bound_mode = "lower"

    elif key_matrix_category == 7:

        header_spec = "TIP Compliance"

        bound_mode = "higher"

    elif key_matrix_category == 8:

        header_spec = "Diary Compliance"

        bound_mode = "higher"

    elif key_matrix_category == 9:

        header_spec = "Quality Review"

        bound_mode = "lower"

    elif key_matrix_category == 10:

        header_spec = "PSR Audit"

        bound_mode = "higher"

   

    # gets minimum values from table

    def create_min_array(df_matrix, category_id):

        min_array = []

        filtered_df = df_matrix[df_matrix["CATEGORY_ID"] == category_id]

        for idx, row in filtered_df.iterrows():

            min_array.append(str(row["MIN_VALUE"]))

        return min_array

 

    # gets maximum values from table

    def create_max_array(df_matrix, category_id):

        max_array = []

        filtered_df = df_matrix[df_matrix["CATEGORY_ID"] == category_id]

        for idx, row in filtered_df.iterrows():

            max_array.append(str(row["MAX_VALUE"]))

        return max_array

 

    # get the min and max values into variables

    max_df = create_max_array(df_matrix, key_matrix_category)

    min_df = create_min_array(df_matrix, key_matrix_category)

 

 

    st.subheader(f'Edit KPI Matrix: {header_spec}', divider='blue')

   

    # place the data forms into columns to get score bounds from user

    col1, col2 = st.columns(2)

    with col1:

 

        st.subheader("Score:")

        min_value_score_1 = st.text_input("Min Value", min_df[0], key="min_value_score_1")

        st.subheader("Score:")

        min_value_score_2 = st.text_input("Min Value:", min_df[1], key="min_value_score_2")

        st.subheader("Score:")

        min_value_score_3 = st.text_input("Min Value", min_df[2], key="min_value_score_3")

        st.subheader("Score:")

        min_value_score_4 = st.text_input("Min Value:", min_df[3], key="min_value_score_4")

        st.subheader("Score:")

        min_value_score_5 = st.text_input("Min Value:", min_df[4], key="min_value_score_5")

        st.button("Back", help="Return to Adjuster Matrix.", on_click=change_page, args=('kpi_matrix',))

 

    with col2:

        st.subheader("1")

        max_value_score_1 = st.text_input("Max Value", max_df[0], key="max_value_score_1")

        st.subheader("2")

        max_value_score_2 = st.text_input("Max Value:", max_df[1], key="max_value_score_2")

        st.subheader("3")

        max_value_score_3 = st.text_input("Max Value", max_df[2], key="max_value_score_3")

        st.subheader("4")

        max_value_score_4 = st.text_input("Max Value:", max_df[3], key="max_value_score_4")

        st.subheader("5")

        max_value_score_5 = st.text_input("Max Value:", max_df[4], key="max_value_score_5")

 

        orig_vals = [

            min_df, max_df

        ]

        # place all user score inputs into a array of tuples

        updates = [

            (key_matrix_category, min_value_score_1, max_value_score_1, 1),

            (key_matrix_category, min_value_score_2, max_value_score_2, 2),

            (key_matrix_category, min_value_score_3, max_value_score_3, 3),

            (key_matrix_category, min_value_score_4, max_value_score_4, 4),

            (key_matrix_category, min_value_score_5, max_value_score_5, 5),

            ]

        st.button(label="Submit", help="Confirm Changes to Score Bounds.", on_click=update_score_value, args=(session, updates, orig_vals, bound_mode,))

           

#############################################################

#

# logic for the edit weights page

#

#############################################################

 

elif st.session_state['current_page'] == 'edit_weights':

    # st.write(st.session_state)

 

    df_matrix = get_score_cat()

   

    def create_weights_array(df_matrix):

        weights_array = []

        for idx, row in df_matrix.iterrows():

            weights_array.append(str(row["WEIGHT"]))

        return weights_array

   

    weights_array = create_weights_array(df_matrix)

           

    # text input weights for all KPIs

    st.subheader('Edit KPI Weights', divider='blue')

 

    #set up in columns

    col1, col2 = st.columns(2)

    with col1:

        weight1 = st.text_input("Production Dollars Weight:", weights_array[0])       

        weight2 = st.text_input("First Contact Weight:", weights_array[1])

        weight3 = st.text_input("First Visit Weight:", weights_array[2])

        weight4 = st.text_input("First Visit to Estimate Weight:", weights_array[3])

        weight5 = st.text_input("First Report Weight:", weights_array[4])

        # create a back button

        st.button('Back', help="Return to Adjuster Matrix.", key="edit_weights_back", on_click=change_page, args=('kpi_matrix',))

 

    with col2:

        weight6 = st.text_input("Estimate Return Weight:", weights_array[5])

        weight7 = st.text_input("TIP Compliance Weight:", weights_array[6])

        weight8 = st.text_input("Diary Compliance Weight:", weights_array[7])

        weight9 = st.text_input("Quality Review Weight:", weights_array[8])

        weight10 = st.text_input("PSR Audit Weight:", weights_array[9])

 

        #put into array to pass into the update function

        edited_weights = [(1, weight1), (2, weight2), (3, weight3), (4, weight4), (5, weight5), (6, weight6),

                      (7, weight7), (8, weight8), (9, weight9), (10, weight10)]

        # create a submit button

        st.button(label="Submit Weights", help="Confirm Changes to Weights.",

                    on_click=update_weight_value, args=(session, edited_weights, weights_array))

 

   

#############################################################

#

# logic for the add subscription page

#

#############################################################

 

elif st.session_state['current_page'] == 'add_sub':

    st.header('Add Regional Subscription', divider="blue")

 

    branch_number = st.text_input("Branch Number")

    service_center_long_name = st.text_input("Service Center")

    manager_name = st.text_input("Manager Name")

    manager_email = st.text_input("Manager Email")

    employee_number = st.text_input("Employee Number")

    is_regional_manager = st.checkbox("Regional Manager")

   

    col1, col2 = st.columns(2)

    with col1:

        st.button("Back", help="Return to Regional Subscriptions", on_click=change_page, args=('regional_subs',))

    with col2:   

        st.button(label="Submit", help="Add Data to Database", on_click=add_reg_sub, args=(session, branch_number, service_center_long_name, manager_name, manager_email, employee_number, is_regional_manager))

 

 

#############################################################

#

# logic for the default edit regional subs page

#

#############################################################

 

elif st.session_state['current_page'] == 'edit_sub':

    st.header("Edit Regional Subscription", divider="blue")

 

    df = get_sub_editable(st.session_state.editID)

    filtered_df = df[df["SUBSCRIPTION_ID"] == st.session_state.editID]

 

    st.text_input("Subscription ID", filtered_df["SUBSCRIPTION_ID"].iloc[0], disabled=True)

    branch_number = st.text_input("Branch Number", filtered_df["SERVICE_CENTER_BRANCH_NUMBER"].iloc[0])

    service_center_long_name = st.text_input("Service Center", filtered_df["SERVICE_CENTER_LONG_NAME"].iloc[0])

    manager_name = st.text_input("Manager Name", filtered_df["MANAGER_NAME"].iloc[0])

    manager_email = st.text_input("Manager Email", filtered_df["MANAGER_EMAIL"].iloc[0])

    employee_number = st.text_input("Employee Number", filtered_df["EMPLOYEE_NUMBER"].iloc[0])

    is_regional_manager = st.checkbox("Regional Manager", filtered_df["IS_REGIONAL_MANAGER"].iloc[0])

 

    col1, col2 = st.columns(2)

    with col1:

        st.button("Back", help="Return to Regional Subscriptions", on_click=change_page, args=('regional_subs',))

    with col2:   

        st.button(label="Submit", help="Add to Database", on_click=add_reg_sub, args=(session, branch_number, service_center_long_name, manager_name, manager_email, employee_number, is_regional_manager))

 

 

#############################################################

#

# logic for the default home content page

#

#############################################################

 

else:

    st.title("Welcome to the US Loss Adjusting Reference Data Application!")

    st.write("")

    st.subheader("Click any option from the sidebar to get started.")
