import argparse
import os

from aiohttp import web

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = [
	# "https://www.googleapis.com/auth/contacts.readonly",
	"https://www.googleapis.com/auth/gmail.readonly",
]
REDIRECT_URI = "http://localhost:8093/redirect-handler"

async def handle_redirect(request):
	name = request.match_info.get("name", "Anonymous")
	for k, v in request.query.items():
		print(k, v)
	state = request.query.get("state")
	code = request.query.get("code")
	scope = request.query.get("scope")

	print(f"code: {code}")
	flow = app["flow"]
	flow.fetch_token(code=code)
	creds = flow.credentials
	app["credentials"] = creds
	with open("token.json", "w") as token:
		token.write(creds.to_json())
		print("wrote credentials")

	return web.Response(text="Thanks, done.")

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("-p", "--port", default=8093)
	args = parser.parse_args()

	creds = None
	if os.path.exists("token.json"):
		creds = Credentials.from_authorized_user_file("token.json", SCOPES)
		use_credentials(creds)
	else:
		creds = do_flow(args.port)

def do_flow(port: int):
	flow = InstalledAppFlow.from_client_secrets_file(
		"credentials.json",
		SCOPES,
		redirect_uri=REDIRECT_URI,
	)
	auth_url, _ = flow.authorization_url(prompt="consent")
	print(f"Please navigate your browser to {auth_url}")

	app["flow"] = flow

	web.run_app(app, port=port)

def use_credentials(creds):
	try:
		# Call the Gmail API
		service = build('gmail', 'v1', credentials=creds)
		results = service.users().labels().list(userId='me').execute()
		labels = results.get('labels', [])

		if not labels:
			print('No labels found.')
			return
		print('Labels:')
		for label in labels:
			print(label['name'])
	except HttpError as err:
		print(err)

app = web.Application()
app.add_routes([
	web.get("/redirect-handler", handle_redirect),
])

