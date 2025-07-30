import base64
import logging
import boto3
from odoo import http
from odoo.http import request, Response
from odoo.tools import config

_logger = logging.getLogger(__name__)


class HPDocumentController(http.Controller):

    @http.route('/hp_document/test', type='http', auth='user', methods=['GET'])
    def test_route(self, **kwargs):
        """
        Test route to verify controller is working
        """
        return Response('Controller is working!', content_type='text/plain')

    @http.route('/hp_document/file/<int:attachment_id>', type='http', auth='user', methods=['GET'])
    def serve_file(self, attachment_id, **kwargs):
        """
        Serve S3 files securely through Odoo with authentication.
        Only authenticated users can access files.
        """
        try:
            # Get the attachment
            attachment = request.env['ir.attachment'].browse(attachment_id)
            if not attachment.exists():
                return Response('File not found', status=404)

            # Check if user has access to this attachment
            if not self._can_access_attachment(attachment):
                return Response('Access denied', status=403)

            # Get file content from S3 or database
            file_content, content_type = self._get_file_from_s3_or_database(attachment)
            if not file_content:
                return Response('File not available', status=404)

            # Return file with proper headers
            headers = {
                'Content-Type': content_type or attachment.mimetype or 'application/octet-stream',
                'Content-Disposition': f'inline; filename="{attachment.name}"',
                'Cache-Control': 'private, max-age=3600',  # Cache for 1 hour
            }

            return Response(file_content, headers=headers)

        except Exception as e:
            _logger.error(f"Error serving file {attachment_id}: {e}")
            return Response('Internal server error', status=500)

    @http.route('/hp_document/download/<int:attachment_id>', type='http', auth='user', methods=['GET'])
    def download_file(self, attachment_id, **kwargs):
        """
        Download S3 files securely through Odoo with authentication.
        """
        try:
            # Get the attachment
            attachment = request.env['ir.attachment'].browse(attachment_id)
            if not attachment.exists():
                return Response('File not found', status=404)

            # Check if user has access to this attachment
            if not self._can_access_attachment(attachment):
                return Response('Access denied', status=403)

            # Get file content from S3 or database
            file_content, content_type = self._get_file_from_s3_or_database(attachment)
            if not file_content:
                return Response('File not available', status=404)

            # Return file for download
            headers = {
                'Content-Type': content_type or attachment.mimetype or 'application/octet-stream',
                'Content-Disposition': f'attachment; filename="{attachment.name}"',
                'Cache-Control': 'private, max-age=3600',
            }

            return Response(file_content, headers=headers)

        except Exception as e:
            _logger.error(f"Error downloading file {attachment_id}: {e}")
            return Response('Internal server error', status=500)

    def _can_access_attachment(self, attachment):
        """
        Check if the current user can access this attachment.
        Override this method to implement custom access control.
        """
        # Basic access control - user must be authenticated
        if not request.env.user.has_group('base.group_user'):
            return False

        # Add more specific access control here if needed
        # For example, check if user has access to the related record
        if attachment.res_model and attachment.res_id:
            try:
                related_record = request.env[attachment.res_model].browse(attachment.res_id)
                if related_record.exists():
                    # Add specific access control logic here
                    # For now, allow access if user can read the related record
                    return True
            except Exception:
                pass

        return True

    def _get_file_from_s3_or_database(self, attachment):
        """
        Get file content from S3 or fallback to database.
        Returns (file_content, content_type) or (None, None) if error.
        """
        try:
            # First try to get from S3 if s3_path exists
            if attachment.s3_path:
                s3_result = self._get_file_from_s3(attachment)
                if s3_result[0]:  # If S3 file found
                    return s3_result

            # Fallback to database file (IF NOT HAVE S3 ACCESS YET)
            return self._get_file_from_database(attachment)

        except Exception as e:
            _logger.error(f"Error getting file for attachment {attachment.id}: {e}")
            return None, None

    def _get_file_from_s3(self, attachment):
        """
        Get file content from S3.
        Returns (file_content, content_type) or (None, None) if error.
        """
        try:
            if not attachment.s3_path:
                return None, None

            # Extract S3 key from the CloudFront URL
            # URL format: https://d85r39ril3sob.cloudfront.net/hp_document/filename.ext
            s3_key = attachment.s3_path.split('/hp_document/')[-1] if '/hp_document/' in attachment.s3_path else None
            if not s3_key:
                return None, None

            # Get S3 credentials from config
            aws_access_key_id = config.get('s3.access.key.id')
            aws_secret_access_key = config.get('s3.secret.access.key')
            s3_bucket = config.get('s3.bucket')
            region_name = config.get('s3.region.name')

            if not all([aws_access_key_id, aws_secret_access_key, s3_bucket, region_name]):
                _logger.warning("S3 credentials not configured, falling back to database")
                return None, None

            # Initialize S3 client
            s3 = boto3.client(
                's3',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=region_name
            )

            # Download file from S3
            response = s3.get_object(Bucket=s3_bucket, Key=f"hp_document/{s3_key}")
            file_content = response['Body'].read()
            content_type = response.get('ContentType', attachment.mimetype)

            return file_content, content_type

        except Exception as e:
            _logger.warning(f"Error getting file from S3 for attachment {attachment.id}: {e}")
            return None, None

    def _get_file_from_database(self, attachment):
        """
        Get file content from database (fallback method).
        Returns (file_content, content_type) or (None, None) if error.
        """
        try:
            _logger.info(f"Trying to get file from database for attachment {attachment.id}")
            
            # Try to get file from database
            if attachment.datas:
                _logger.info(f"Found attachment.datas for attachment {attachment.id}")
                file_content = base64.b64decode(attachment.datas)
                content_type = attachment.mimetype or 'application/octet-stream'
                return file_content, content_type

            # If no database file, try to get from filestore
            if attachment.store_fname:
                _logger.info(f"Found attachment.store_fname: {attachment.store_fname}")
                import os
                filestore_path = config.filestore(request.env.cr.dbname)
                file_path = os.path.join(filestore_path, attachment.store_fname)
                _logger.info(f"Looking for file at: {file_path}")
                
                if os.path.exists(file_path):
                    _logger.info(f"File exists at: {file_path}")
                    with open(file_path, 'rb') as f:
                        file_content = f.read()
                    content_type = attachment.mimetype or 'application/octet-stream'
                    return file_content, content_type
                else:
                    _logger.warning(f"File does not exist at: {file_path}")

            _logger.warning(f"No file found for attachment {attachment.id}")
            return None, None

        except Exception as e:
            _logger.error(f"Error getting file from database for attachment {attachment.id}: {e}")
            return None, None