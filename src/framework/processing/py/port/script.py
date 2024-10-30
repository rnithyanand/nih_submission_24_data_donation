import port.api.props as props
from port.api.commands import (CommandUIRender, CommandSystemExit, CommandSystemDonate)
from port.TikTokProcessor.Processor import TikTokDataProcessing
import pandas as pd
import zipfile
from pyodide.http import pyfetch
import asyncio

import json



def process(session_id: str):
    platform = "TikTok Data Donation Research"
    while True:
        file_prompt = generate_file_prompt(platform, "application/zip, application/json")
        file_prompt_result = yield render_page(platform, file_prompt)
        if file_prompt_result.__type__ == 'PayloadString':
            filepath = file_prompt_result.value
            is_data_valid = validate_input_file(filepath)
            print(is_data_valid, filepath)
            if is_data_valid:
                tiktok_processor = TikTokDataProcessing(filepath)
                tiktok_processor.extract_data()
                tiktok_processor.print_summary_data()
                tiktok_processor.get_activity_timeline()
                timeline_data = tiktok_processor.activity_timeline
                # Generate an analysis page with the timeline data
                analysis_prompt = generate_analysis_prompt(timeline_data)
                yield render_page(platform, analysis_prompt)
                # Generate a consent prompt after the analysis
                consent_prompt = generate_consent_prompt(timeline_data)
                consent_prompt_result = yield render_page(platform, consent_prompt)
                if consent_prompt_result.__type__ == "PayloadJSON":
                    yield donate(f"{session_id}-{platform}", consent_prompt_result.value)
                break
            else:
                retry_prompt = generate_retry_prompt(platform)
                retry_prompt_result = yield render_page(platform, retry_prompt)
                if retry_prompt_result.__type__ != 'PayloadTrue':
                    break
        else:
            break
    yield render_end_page()


def generate_analysis_prompt(timeline_data):
    try:
        description = props.Translatable({
            "en": "Here's an analysis of your TikTok activity over time. "
                  "The table below shows your daily activity broken down by type."})
        # Convert timeline_data to a pandas DataFrame
        df = pd.DataFrame(timeline_data).T
        print(df.head(19))
        df.index.name = 'Date'  # Name the index
        df = df.reset_index()  # Reset the index to make 'Date' a column
        df = df.groupby('Date').sum().reset_index()  # Aggregate by day
        ## Ensure 'Date' is datetime type and then format it
        # df['Date'] = pd.to_datetime(df['Date'])
        # df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')  # Format date as string
        print("DataFrame after processing:")
        print(df.head())  # Print first few rows for debugging
        vis_events_1 = dict(title={"en": "Your TikTok Activity Over Time"},
            type="line",
            group=dict(column="Date", dateFormat="hour", label="Hour"),
            values=[dict(label='# of Events', column="n_events", aggregate='sum'), ])
        vis_events_2 = dict(title={"en": "Your TikTok Video Consumption and Creation Activity Over Time"},
            type="line",
            group=dict(column="Date", dateFormat="hour", label="Hour"),
            values=[dict(label='# of Videos Browsed', column="browsed", aggregate='sum'),
                dict(label='# of Videos Shared', column="shared", aggregate='sum'),
                dict(label='# of Comments Made', column="commented", aggregate='sum'),
                dict(label='# of Videos Liked', column="liked", aggregate='sum'),
                dict(label='# of Videos Posted', column="posted", aggregate='sum'), ])
        vis_events_3 = dict(title={"en": "Your TikTok DMing and Shopping Activity Over Time"},
            type="line",
            group=dict(column="Date", dateFormat="hour", label="Hour"),
            values=[dict(label='# of DMs Sent/Received', column="dmed", aggregate='sum'),
                dict(label='# of Products Browsed', column="product_browsed", aggregate='sum'), ])
        table = props.PropsUIPromptConsentFormTable(id="activity_timeline",
            title=props.Translatable({"en": "Your TikTok Activity Over Time"}),
            data_frame=df,
            visualizations=[vis_events_1, vis_events_2, vis_events_3])
        return props.PropsUIPromptConsentForm([table], [], description=description)
    except Exception as e:
        print(f"Error in generate_analysis_prompt: {str(e)}")
        print("Timeline data:")
        print(timeline_data)
        raise  # Re-raise the exception after printing debug info


def generate_consent_prompt(timeline_data):
    description = props.Translatable({"en": "Below is a summary of your TikTok activity. "
                                            "Please review this data carefully. "
                                            "If you're comfortable sharing this information for research purposes, "
                                            "click 'Yes, share for research' at the bottom of the page."})
    donate_question = props.Translatable({"en": "Do you want to share this data for research?"})
    donate_button = props.Translatable({"en": "Yes, share for research"})
    df = pd.DataFrame(timeline_data).T
    df.index.name = 'Date'
    df = df.reset_index()
    table = props.PropsUIPromptConsentFormTable("tiktok_activity_summary",
        props.Translatable({"en": "Your TikTok Activity Summary"}),
        df)
    return props.PropsUIPromptConsentForm([table],
        [],
        description=description,
        donate_question=donate_question,
        donate_button=donate_button)


def donate(key, json_string):
    try:
        # Convert json_string back to a Python object
        data = json.loads(json_string)

        # Prepare the data for sending
        payload = {'key': key, 'data': data}

        # Send the data to your server
        response = requests.post('http://10.128.0.2:5000/api/donate', json=payload)

        if response.status_code == 200:
            print(f"Data successfully donated with key: {key}")
            return CommandSystemDonate(key, json_string)
        else:
            print(f"Failed to donate data. Server responded with status code: {response.status_code}")
            return CommandSystemExit(1, "Failed to donate data")
    except Exception as e:
        print(f"An error occurred while donating data: {str(e)}")
        return CommandSystemExit(1, f"Error donating data: {str(e)}")


def validate_input_file(file_path: str) -> bool:
    try:
        if file_path.endswith('.zip'):
            with zipfile.ZipFile(file_path) as zf:
                return 'user_data_tiktok.json' in zf.namelist()
        elif file_path.endswith('.json'):
            with open(file_path, 'r') as f:
                data = json.load(f)
                return 'video_list' in data
        return False
    except Exception:
        return False


def render_end_page():
    page = props.PropsUIPageEnd()
    return CommandUIRender(page)


def render_page(platform: str, body):
    header = props.PropsUIHeader(props.Translatable({"en": platform}))
    footer = props.PropsUIFooter()
    page = props.PropsUIPageDonation(platform, header, body, footer)
    return CommandUIRender(page)


def generate_retry_prompt(platform: str) -> props.PropsUIPromptConfirm:
    text = props.Translatable({"en": f"Unfortunately, we cannot process your {platform} data donation. "
                                     f"Continue if you are sure that you selected the right file. "
                                     f"Try again to select a different file."})
    ok = props.Translatable({"en": "Try again"})
    cancel = props.Translatable({"en": "Continue"})
    return props.PropsUIPromptConfirm(text, ok, cancel)


def generate_file_prompt(platform, extensions) -> props.PropsUIPromptFileInput:
    description = props.Translatable({"en": f"""To participate in this study, you need to upload your TikTok data. Here's how to get it:
    
1. Open TikTok, click on your profile picture on the top right corner.
2. Click the 'Settings' option.
3. Select the 'Manage account' tab.
4. Click the 'Download your data' option.
5. Choose 'All data' and select 'JSON' as the file format.
6. Submit your request by clicking the red 'Request data' button.

7. Wait for TikTok to prepare your data (you will get an email when this process is complete; this may take a few hours).
8. Once the data is ready, download your data file.
9. Upload the downloaded ZIP file here.

Important: We only need specific information from your data for this study. You'll be able to review exactly what's being shared before you decide to donate.

Click "Choose file" below to select and upload your TikTok data file."""})
    return props.PropsUIPromptFileInput(description, extensions)


def exit_port(code, info):
    return CommandSystemExit(code, info)
