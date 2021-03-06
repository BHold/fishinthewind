import mimetypes

from storages.backends.s3boto import S3BotoStorage
from boto.s3.key import Key


class StaticToS3Storage(S3BotoStorage):
    """
    Staticfile storage class to files to s3

    Needed to override save() in order to set rewind to True in set_contents_from_file call
    """
    def save(self, name, content):
        cleaned_name = self._clean_name(name)
        name = self._normalize_name(cleaned_name)
        headers = self.headers.copy()
        content_type = getattr(content, 'content_type', mimetypes.guess_type(name)[0] or Key.DefaultContentType)

        if self.gzip and content_type in self.gzip_content_types:
            content = self._compress_content(content)
            headers['Content-Encoding'] = 'gzip'

        content.name = cleaned_name
        k = self.bucket.get_key(self._encode_name(name))
        if not k:
            k = self.bucket.new_key(self._encode_name(name))

        k.set_metadata('Content-Type', content_type)
        k.set_contents_from_file(content, headers=headers, policy=self.acl,
                                 reduced_redundancy=self.reduced_redundancy, rewind=True)
        return cleaned_name
