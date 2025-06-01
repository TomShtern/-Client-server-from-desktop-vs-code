# Secure File Backup Server

This is a simple file backup server that accepts file uploads over HTTP with basic authentication.

## Server Setup

1. Make sure you have Python 3.x installed
2. Run the server:

   ```python
   python server.py
   ```

3. The server will start and listen on port 8080

## Server Configuration

You can modify the following variables in `server.py`:

- `BACKUP_DIR`: Directory where uploaded files are stored (default: 'backups')
- `USERNAME`: Username for authentication (default: 'user')
- `PASSWORD`: Password for authentication (default: 'password')

## Security Notes

- The server uses basic authentication, which sends credentials in base64 encoding.
- For production use, consider adding SSL/TLS encryption or using a reverse proxy with HTTPS.

## Server API

### Uploading files

- **URL**: `http://localhost:8080`
- **Method**: POST
- **Headers**:
  - `Authorization`: Basic authentication header
  - `X-Filename`: Name of the file to be uploaded (optional)
- **Body**: Binary file content
- **Response**: Status code 200 on success with message

### Status page

- **URL**: `http://localhost:8080`
- **Method**: GET
- **Response**: HTML page showing server status and recent uploads

## File Storage

Files are stored in the `backups` directory with the following structure:
  
backups/
  ├── YYYY-MM-DD_HH-MM-SS_filename.ext
  ├── YYYY-MM-DD_HH-MM-SS_filename2.ext
  └── ...

```text
backups/
  ├── 2024-06-01_12-00-00_document.pdf
  ├── 2024-06-01_12-05-30_photo.jpg
  └── ...
```

## Logging

The server logs all activities to `backup_server.log` in the same directory as the server script.
