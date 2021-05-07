# Synology NAS REST API Python client

### How To
```
import synology

key = synology.login()

synology.download_file(key, 'path/to/file.pdf')

synology.create_folder(key, 'path/to/folder')

synology.upload(key,'/local/file/path.pdf','/remote/file/path.pdf')

synology.logout(key)
```
