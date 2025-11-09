import json
from time import sleep

import requests

URL = "www.prism-challenge.com"
PORT = 8082

# Please do NOT share this information anywhere, unless you want your team to be cooked.
TEAM_API_CODE = "4bf04deddec8f60738c8ea8786f40862" # OURS
# TEAM_API_CODE = "d3e63892502a2bf7839f3dc7b0f26801"

def sendGetRequest(path):
	"""
	Sends a HTTP GET request to the server.
	Returns:
		(success?, error or message)
	"""
	headers = {"X-API-Code": TEAM_API_CODE}
	response = requests.get(f"http://{URL}:{PORT}/{path}", headers=headers)

	# Check whether there was an error sent from the server.
	# 200 is the HTTP Success status code, so we do not expect any
	# other response code.
	if response.status_code != 200:
		return (
			False,
			f"Error - something went wrong when requesting [CODE: {response.status_code}]: {response.text}",
		)
	return True, response.text

def sendPostRequest(path, data=None):
	"""
	Sends a HTTP POST request to the server.
	Pass in the POST data to data, to send some message.
	Returns:
		 (success?, error or message)
	"""
	headers = {"X-API-Code": TEAM_API_CODE, "Content-Type": "application/json"}

	# Convert the data from python dictionary to JSON string,
	# which is the expected format to be passed
	data = json.dumps(data)
	response = requests.post(f"http://{URL}:{PORT}/{path}", data=data, headers=headers)

	# Check whether there was an error sent from the server.
	# 200 is the HTTP Success status code, so we do not expect any
	# other response code.
	if response.status_code != 200:
		return (
			False,
			f"Error - something went wrong when requesting [CODE: {response.status_code}]: {response.text}",
		)
	return True, response.text

def getContext():
	"""
	Query the challenge server to request for a client to design a portfolio for.
	Returns:
		(success?, error or message)
	"""
	return sendGetRequest("/request")

def getMyCurrentInformation():
	"""
	Query your team information.
	Returns:
		(success?, error or message)
	"""
	return sendGetRequest("/info")

def sendPortfolio(weightedStocks):
	"""
	Send portfolio stocks to the server for evaluation.
	Returns:
		(success?, error or message)
	"""
	# data = [
	# 	{"ticker": weighted_stock[0], "quantity": weighted_stock[1]}
	# 	for weighted_stock in weighted_stocks
	# ]
	return sendPostRequest("/submit", data=weightedStocks)
