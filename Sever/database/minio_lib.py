from minio import Minio as main_minio
from Sever.configs import minio_conf
from minio import error

client = main_minio(minio_conf.URL,
                    access_key=minio_conf.ACCESS_KEY,
                    secret_key=minio_conf.SECRET_KEY,
                    secure=False)


def initialize_minio(Bucket: str = None):

    if not client.bucket_exists(Bucket):
        try:
            client.make_bucket(Bucket)
        except error.BucketAlreadyOwnedByYou as err:
            pass
        except error.BucketAlreadyExists as err:
            pass
        except error.ResponseError as err:
            raise
    else:
        return Bucket
