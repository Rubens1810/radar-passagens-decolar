import json
from src.main import run


def lambda_handler(event, context):
    print("🚀 Iniciando execução agendada do Radar de Passagens na AWS Lambda...")
    run()
    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Varredura concluída com sucesso!"}),
    }