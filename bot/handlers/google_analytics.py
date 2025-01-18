from google.analytics.data import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest
from google.oauth2 import service_account


from bot.config.settings import settings


# Replace with your Google Analytics property ID
PROPERTY_ID = settings.ga_id
credentials = service_account.Credentials.from_service_account_file(
    settings.ga_credentials
)
analytics_client = BetaAnalyticsDataClient(credentials=credentials)

print(analytics_client)

def format_response(response):
    """
    Format the Google Analytics API response into a human-readable dictionary.
    """
    if not response.rows:
        return "No data available for the selected query."

    formatted_data = []
    for row in response.rows:
        row_data = {dimension.name: value for dimension, value in zip(response.dimension_headers, row.dimension_values)}
        row_data.update({metric.name: value for metric, value in zip(response.metric_headers, row.metric_values)})
        formatted_data.append(row_data)
    
    return formatted_data

def get_analytics_data():
    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[{"name": "city"}],
        metrics=[{"name": "activeUsers"}],
        date_ranges=[{"start_date": "7daysAgo", "end_date": "today"}],
    )

    response = analytics_client.run_report(request)
    data = []

    for row in response.rows:
        data.append({
            "dimension": row.dimension_values[0].value,
            "metric": row.metric_values[0].value,
        })

    return data

def get_daily_registrations():
    """
    Fetch daily registrations from Google Analytics.
    """
    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        date_ranges=[{"start_date": "yesterday", "end_date": "yesterday"}],
        dimensions=[{"name": "date"}],
        metrics=[{"name": "eventCount"}],
        dimension_filter={"filter": {
            "field_name": "eventName",
            "string_filter": {"value": "register"}
        }},
    )

    try:
        response = analytics_client.run_report(request)
        return format_response(response)
    except Exception as e:
        return f"Error fetching daily registrations: {e}"

def get_daily_referrals():
    """
    Fetch daily referral counts grouped by source or referrer.
    """
    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        date_ranges=[{"start_date": "yesterday", "end_date": "yesterday"}],
        dimensions=[{"name": "eventName"}, {"name": "customEvent:ref"}],  # Use the correct custom dimension
        metrics=[{"name": "eventCount"}],
        dimension_filter={"filter": {
            "field_name": "eventName",
            "string_filter": {"value": "ref"}
        }},
    )

    try:
        response = analytics_client.run_report(request)
        return format_response(response)
    except Exception as e:
        return f"Error fetching referrals: {e}"

def get_onboarding_data():
    """
    Fetch data for onboarding completion and skips.
    """
    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        date_ranges=[{"start_date": "yesterday", "end_date": "yesterday"}],
        dimensions=[{"name": "eventName"}],
        metrics=[{"name": "eventCount"}],
        dimension_filter={"filter": {
            "field_name": "eventName",
            "in_list_filter": {"values": ["onboarding_complete", "onboarding_skip"]}
        }},
    )

    try:
        response = analytics_client.run_report(request)
        return format_response(response)
    except Exception as e:
        return f"Error fetching onboarding data: {e}"


def get_wallet_connections():
    """
    Fetch data for wallet connections (connect_wallet).
    """
    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        date_ranges=[{"start_date": "yesterday", "end_date": "yesterday"}],
        dimensions=[{"name": "date"}],
        metrics=[{"name": "eventCount"}],
        dimension_filter={"filter": {
            "field_name": "eventName",
            "string_filter": {"value": "connect_wallet"}
        }},
    )

    try:
        response = analytics_client.run_report(request)
        return format_response(response)
    except Exception as e:
        return f"Error fetching wallet connections: {e}"

def get_exercise_purchases():
    """
    Fetch data for exercise purchases (exercise_buy).
    """
    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        date_ranges=[{"start_date": "yesterday", "end_date": "yesterday"}],
        dimensions=[{"name": "eventName"}, {"name": "customEvent:alias"}, {"name": "customEvent:id"}],
        metrics=[{"name": "eventCount"}],
        dimension_filter={"filter": {
            "field_name": "eventName",
            "string_filter": {"value": "exercise_buy"}
        }},
    )

    try:
        response = analytics_client.run_report(request)
        return format_response(response)
    except Exception as e:
        return f"Error fetching exercise purchases: {e}"

def get_camera_events():
    """
    Fetch camera-related events (on, error, not allowed).
    """
    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        date_ranges=[{"start_date": "yesterday", "end_date": "yesterday"}],
        dimensions=[{"name": "eventName"}],
        metrics=[{"name": "eventCount"}],
        dimension_filter={"filter": {
            "field_name": "eventName",
            "in_list_filter": {"values": ["camera_on", "camera_error", "camera_not_allowed"]}
        }},
    )

    try:
        response = analytics_client.run_report(request)
        return format_response(response)
    except Exception as e:
        return f"Error fetching camera events: {e}"

if __name__ == "__main__":
    print("Daily Registrations:")
    print(get_daily_registrations())

    print("Daily Referrals:")
    print(get_daily_referrals())

    print("Onboarding Data:")
    print(get_onboarding_data())

    print("Wallet Connections:")
    print(get_wallet_connections())

    print("Exercise Purchases:")
    print(get_exercise_purchases())

    # print("Camera Events:")
    # print(get_camera_events())