import json
import logging
import os
import sys
import urllib
from datetime import datetime

# PATHS
BASE_PATH = '/path/to/some/shared/folder'
BASE_OLD_PATH = '/path/to/another/shared/folder'

# FILE EXTENSION
EXT = '.csv'

def login():
	"""Login and request sessioon cookie on Synology NAS

	Note: https://global.download.synology.com/download/Document/Software/DeveloperGuide/Package/FileStation/All/enu/Synology_File_Station_API_Guide.pdf

	Returns:
		string: Sessio ID (cookie). Empty if login failed.
	"""
	LOGIN_URL = 'http://{NAS_IP}:5000/webapi/auth.cgi?api=SYNO.API.Auth&version=3&method=login&account={USERNAME}&passwd={PASSWORD}&session=FileStation&format=cookie'
	
	try:
		login_request = requests.get(LOGIN_URL)
		login_data = login_request.json()
	except:
		print 'log error'
		return ''

	try:
		session_id = login_data["data"]["sid"]
		logger.info('Login on NAS API OK, cookie: {}'.format(session_id))
		return session_id
	except:
		print 'log error'
		return ''

def check_file(sid, file_name):
	"""Check if file exist on Synology NAS

	Note: https://global.download.synology.com/download/Document/Software/DeveloperGuide/Package/FileStation/All/enu/Synology_File_Station_API_Guide.pdf

	Args:
		sid (str): Session ID (cookie)
		file_name (str): File name, with extension and without any path

	Returns:
		bool: True if exists, False if not found

	"""
	final_path = urllib.quote_plus(BASE_PATH + '/' + file_name + EXT)
	info_url = 'http://{NAS_IP}:5000/webapi/entry.cgi?api=SYNO.FileStation.List&method=getinfo&version=2&path=' + final_path +'&additional=time&_sid=' + sid
	
	try:
		info_request = requests.get(info_url)
		info_data = info_request.json()
	except:
		logger.error('Error accesing NAS API')
		return False

	try:
		error_code = info_data["data"]["files"][0]["code"]
		if (error_code == 408):
			logger.info('File {}.csv not found on NAS'.format(file_name))
			return False
	except:
		logger.info('Found {} file on NAS'.format(file_name + EXT))
		return True

	return True
	
def get_file_date(sid, file_name):
	"""Get last modification date of file on Synology NAS

	Note: https://global.download.synology.com/download/Document/Software/DeveloperGuide/Package/FileStation/All/enu/Synology_File_Station_API_Guide.pdf

	Args:
		sid (str): Session ID (cookie)
		file_name (str): File name, with extension and without any path

	Returns:
		string: Last modification date of file

	"""
	final_path = urllib.quote_plus(BASE_PATH + '/' + file_name + EXT)
	info_url = 'http://{NAS_IP}:5000/webapi/entry.cgi?api=SYNO.FileStation.List&method=getinfo&version=2&path=' + final_path +'&additional=time&_sid=' + sid

	try:
		info_request = requests.get(info_url)
		info_data = info_request.json()
	except:
		logger.error('Error accesing NAS API')

	try:
		file_date = info_data["data"]["files"][0]["additional"]["time"]["ctime"]
	except:
		logger.error('Error getting date from json file on get_file_date request')
		return ''

	final_date = datetime.fromtimestamp(file_date)
	logger.info('Last modification of {} is: {}'.format((file_name + EXT), final_date))

	return final_date.strftime('%Y%m%d')
	
def check_folder(sid, folder_name):
	"""Check if folder exists on Synology NAS
	
	Note: https://global.download.synology.com/download/Document/Software/DeveloperGuide/Package/FileStation/All/enu/Synology_File_Station_API_Guide.pdf

	Args:
		sid (str): Session ID (cookie)
		folder_name (str): Folder name
		
	Returns:
		bool: True if folder found, False if not
	"""
	FOLDER_INFO_URL = 'http://{NAS_IP}:5000/webapi/entry.cgi?api=SYNO.FileStation.List&method=getinfo&version=2&path='
	target_folder_path = urllib.quote_plus(BASE_OLD_PATH + '/' + folder_name)
	check_folder_url = FOLDER_INFO_URL + target_folder_path + '&_sid=' + sid

	try:
		check_dir_req = requests.get(check_folder_url)
		check_dir_res = check_dir_req.json()
	except:
		logger.error('Error accesing NAS API')
		return False

	try:
		if (check_dir_res["data"]["files"][0]["code"] == 408):
			logger.info('Folder {} not found on NAS'.format(folder_name))
			return False
	except:
		logger.info('Found {} folder on NAS'.format(folder_name))
		return True
		
def create_folder(sid, folder_name):
	"""Create a folder on Synology NAS
	
	Note: https://global.download.synology.com/download/Document/Software/DeveloperGuide/Package/FileStation/All/enu/Synology_File_Station_API_Guide.pdf

	Args:
		sid (str): Session ID (cookie)
		folder_name (str): Folder name
		
	Returns:
		bool: True if success, False if fails
	"""	
	DIR_URL = 'http://{NAS_IP}:5000/webapi/entry.cgi?api=SYNO.FileStation.CreateFolder&method=create&version=2&folder_path='
	create_url = DIR_URL + urllib.quote_plus(BASE_OLD_PATH) + '&name=' + folder_name + '&_sid=' + sid
	new_folder_path = urllib.quote_plus(BASE_OLD_PATH + '/' + folder_name)
	
	try:	
		create_folder_req = requests.get(create_url)
		create_folder_res = create_folder_req.json()
	except:
		logger.error('Error on create_folder request')
		return False

	try:
		create_result = create_folder_res["success"]
		if (create_result):
			logger.info('Folder {} created successfuly'.format(folder_name))
			return True
		else:
			logger.error('Error creating {} folder'.format(folder_name))
	except:
		logger.error('Error getting json file from create_folder')
		return False
		
def move_file(sid, file_name):
	"""Move a file on Synology NAS
	
	Note: https://global.download.synology.com/download/Document/Software/DeveloperGuide/Package/FileStation/All/enu/Synology_File_Station_API_Guide.pdf

	Args:
		sid (str): Session ID (cookie)
		file_name (str): File name, with extension and without any path
		
	Returns:
		bool: True if success, False if fails
	"""
	STATUS_URL = 'http://{NAS_IP}:5000/webapi/entry.cgi?api=SYNO.FileStation.CopyMove&version=1&method=status&taskid='
	MOVE_URL = 'http://{NAS_IP}:5000/webapi/entry.cgi?api=SYNO.FileStation.CopyMove&version=3&method=start&overwrite=true&remove_src=true&path='
	move_from = urllib.quote_plus(BASE_PATH + '/' + file_name + EXT)
	move_to = urllib.quote_plus(BASE_OLD_PATH + '/' + file_name)
	url_move = MOVE_URL + move_from + '&dest_folder_path=' + move_to + '&_sid=' + sid

	# check if folder exists #

	try:
		move_request = requests.get(url_move)
		move_data = move_request.json()
	except:
		logger.error('Error accesing NAS API')
		return False

	task_id = ""
	
	try:
		task_id = move_data["data"]["taskid"]
	except:
		logger.error('Error getting json from move_file request')
		return False

	# check status
	url_status = STATUS_URL + task_id + "_&sid" + sid

	try:
		status_request = requests.get(url_status)
	except:
		logger.error('Error accesing NAS API')
		return False

	try:
		if status_request.status_code is 200:
			logger.info('File moved successfuly')
			return True
	except:
		logger.error('Error moving file {}'.format(file_name))
		return False

	return False
	
def rename_file(sid, file_name, file_date):
	"""Rename a file on Synology NAS
	
	Note: https://global.download.synology.com/download/Document/Software/DeveloperGuide/Package/FileStation/All/enu/Synology_File_Station_API_Guide.pdf

	Args:
		sid (str): Session ID (cookie)
		file_name (str): File name, with extension and without any path
		
	Returns:
		bool: True if success, False if fails
	"""
	target_file = urllib.quote_plus(BASE_OLD_PATH + '/' + file_name + '/' + file_name + EXT)
	new_name = file_date + '_' + file_name + EXT
	rename_url = 'http://{NAS_IP}:5000/webapi/entry.cgi?api=SYNO.FileStation.Rename&version=1&method=rename&path=' + target_file + '&name=' + new_name + '&_sid=' + sid

	try:
		rename_req = requests.get(rename_url)
                rename_res = rename_req.json()
                
		if (rename_res["success"]): 
		    logger.info('File {} renamed to {} successfuly'.format((file_name + EXT), new_name ))
		    return True
		else:
		    logger.warning('File {} not renamed to {}. Already exists.'.format(file_name + EXT, new_name))
		    return False
	except:
		logger.error('Error on renaming request of file: {}'.format(file_name + EXT))
		return False

def download_file(sid, file_name):
	"""Download a file from the Synology NAS
	
	Note: https://global.download.synology.com/download/Document/Software/DeveloperGuide/Package/FileStation/All/enu/Synology_File_Station_API_Guide.pdf

	Args:
		sid (str): Session ID (cookie)
		file_name (str): File name, with extension and without any path
		
	Returns:
		bool: True if success, False if fails
	"""
	DOWNLOAD_URL = 'http://{NAS_IP}:5000/webapi/entry.cgi?api=SYNO.FileStation.Download&version=2&method=download&path='
	final_path = urllib.quote_plus(BASE_PATH + '/' + file_name)
	url_download = DOWNLOAD_URL + final_path + '&mode=download&_sid=' + sid
	download_request = requests.get(url_download, stream=True)
	with open(file_name, 'wb') as tmp_file:
		for chunk in download_request.iter_content(chunk_size=8192):
			if chunk:
				tmp_file.write(chunk)

	if (os.path.isfile(file_name)):
		return True
		logger.info('Download {} successfuly'.format(file_name))
	else:
		logger.error('File {} failed to download'.format(file_name))
		return False
		
def upload_file(sid, tab_name, file_name):
	"""Upload a file to the Synology NAS
	
	Note: https://global.download.synology.com/download/Document/Software/DeveloperGuide/Package/FileStation/All/enu/Synology_File_Station_API_Guide.pdf
			
			There's a problem with overwrite. The funcion is not overwriting the festination file if already exists

	Args:
		sid (str): Session ID (cookie)
		tab (str): Tab name, aka filename without extension
		file_name (str): File name, with extension and without any path
		
	Returns:
		bool: True if success, False if fails
	"""
	UPLOAD_URL = 'http://{NAS_IP}:5000/webapi/entry.cgi?api=SYNO.FileStation.Upload&version=3&method=upload&_sid='
	url_upload = UPLOAD_URL + sid
	try:
		session_upload = requests.session()
		with open(file_name, 'rb') as payload:
			args = {
				'path': BASE_PATH,
				'create_parents': False,
				'overwrite': True,
			}
			files = {'file': (file_name, payload, 'application/octect-stream')}
			k = session_upload.post (url_upload, data=args, files=files)

		if (k.status_code is 200 and k.json()['success']):
			logger.info('{} file upload successfuly to {}'.format(file_name, BASE_PATH))
			return True
	except:
		logger.error('{} failed to upload to {}'.format(file_name, BASE_PATH))
		return False
		
def logout(sid):
	"""Logout from Synology NAS = destroy session cookie

	Note: https://global.download.synology.com/download/Document/Software/DeveloperGuide/Package/FileStation/All/enu/Synology_File_Station_API_Guide.pdf
	
	Args:
		sid (str): Session ID (cookie)

	Returns:
		bool: True if success, False if fails
	"""
	logout_session = requests.get(LOGOUT_URL + sid)
	if (logout_session.status_code is 200):
		logger.info('Logout successfuly from NAS API session: {}'.format(sid))
		return True
	else:
		logger.error('Logout error for session {} on NAS API'.format(sid))
		return False
