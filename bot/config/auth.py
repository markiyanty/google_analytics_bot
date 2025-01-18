from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import json, os, time, webbrowser
from queue import Queue
from bot.config.settings import settings
from bot.server import start_local_server, OAuthRedirectHandler


auth_response = None  # Global variable to store the OAuth response

def authenticate(host='localhost', port=8081, method='http'):
    """Handles Google OAuth authentication with a local server."""
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Allow insecure transport (for local development only)
    
    # Create the OAuth flow
    flow = Flow.from_client_secrets_file(
        settings.gm_credentials,
        scopes=['https://www.googleapis.com/auth/calendar'],
        redirect_uri=f"http://{host}:{port}"
    )
    
    # Create a queue for inter-process communication
    auth_queue = Queue()
    server = start_local_server(port=port, queue=auth_queue)  # Start the server

    # Generate the authorization URL
    auth_url, _ = flow.authorization_url(prompt='consent')
    webbrowser.open(auth_url)  # Open the browser for user authentication
    
    # Wait for the authorization response
    auth_response = auth_queue.get()  # Wait for the response to be put into the queue
    print(f"Authorization response received: {auth_response}")

    # Fetch the token using the response
    try:
        flow.fetch_token(authorization_response=f"http://{host}:{port}{auth_response}")
        print("Token fetched successfully")
    except Exception as e:
        print(f"Error fetching token: {e}")
        server.shutdown()
        return None
    
    # Shut down the server
    server.shutdown()

    # Get credentials
    credentials = flow.credentials
    if credentials is None or not credentials.token:
        print("Error: Credentials could not be retrieved.")
        return None

    return credentials

def get_google_auth_url(host='localhost', port:int=8081):
    flow = Flow.from_client_secrets_file(
        settings.gm_credentials,  # Your OAuth credentials file
        scopes='https://www.googleapis.com/auth/calendar',
        redirect_uri=f'http://{host}:{port}/callback'
    )
    auth_url, _ = flow.authorization_url(prompt='consent')
    return auth_url

#deprecated
def get_google_auth_url(port: int=8081, host='localhost', manual_flow=False):
    flow = Flow.from_client_secrets_file(
        settings.gm_credentials,
        scopes='https://www.googleapis.com/auth/calendar',
        redirect_uri='urn:ietf:wg:oauth:2.0:oob' if manual_flow else f'http://{host}:{port}'
    )
    auth_url, _ = flow.authorization_url(prompt='consent')
    return auth_url

def exchange_auth_code(auth_code, host='localhost'):
    flow = Flow.from_client_secrets_file(
        settings.gm_credentials,
        scopes='https://www.googleapis.com/auth/calendar',
        redirect_uri=f'http://{host}'
    )
    flow.fetch_token(code=auth_code)
    return flow.credentials
