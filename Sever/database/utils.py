from flask import jsonify
import base64
import io
from Sever.database import minio_lib


def from_b64str_to_minio(mime_types: dict,
                         data: str,
                         ext: str,
                         minio_id: str,
                         bucket_name: str):
    """
    Запись файла из base64 строки в minio без сохранения локально
    """
    try:
        extension = mime_types[ext]
        if 'base64' in data:
            file_content = data.split('base64,')[1]
        else:
            file_content = data

        decoded_data = base64.b64decode(file_content)  # Декодируем base64 сразу в bytes
        value_as_a_stream = io.BytesIO(decoded_data)   # Создаём поток для передачи

        minio_lib.client.put_object(
            bucket_name=minio_lib.initialize_minio(bucket_name),
            object_name=minio_id,
            data=value_as_a_stream,
            length=len(decoded_data),
        )
    except Exception as ex:
        return 0
    return 1

def from_minio_to_b64str(minio_id: str,
                         bucket_name: str) -> str:
    """
    Возврат файла в base64 строки из minio

    params:
    minio_id: путь до minio
    bucket_name: имя bucket в minio
    """
    data = None
    try:
        resp = minio_lib.client.get_object(bucket_name=bucket_name,
                                           object_name=minio_id)
        data = base64.b64encode(resp.data).decode('UTF8')
    except Exception as ex:
        print(ex)
        return None
    return data

def save_file(data, folder, memo_id=None, checklist_id=None):
    """
    Запись файла в минио.
    folder: "contracts", "payments", "justifications"
    """
    mime_types = {
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'application/msword': '.doc',
            'application/pdf': '.pdf',
            'image/jpeg': '.jpeg',
            'image/png': '.png',
            'application/x-zip-compressed': '.zip'
            }
    id = None
    if memo_id and memo_id != 0:
        id = memo_id
    elif checklist_id and checklist_id != 0:
        id = checklist_id
    else:
        raise ValueError("Memo_id or Checklist_if not setted")
    try:         
        minio_id = f"{folder}/{id}/{data['NAME']}{mime_types[data['EXT']]}"
        from_b64str_to_minio(mime_types=mime_types,
                            data=data['DATA'],
                            ext=data['EXT'],
                            minio_id=minio_id,
                            bucket_name='sever')
        return jsonify({"STATUS": "Ok", "ID": str(id)}), 200
    
    except ValueError as ex:
        raise ValueError(f"{ex}")

    except Exception as ex:
       raise RuntimeError(f"{ex}")