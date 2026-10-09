from storages.backends.gcloud import GoogleCloudStorage

class CustomGoogleCloudStorage(GoogleCloudStorage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bucket_name = "editoruploads"