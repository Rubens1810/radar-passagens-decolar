import json
from pathlib import Path
from dotenv import load_dotenv
from src.collector import FlightCollector
from src.notifier import send_discord_alert

load_dotenv()


def run():
    routes_path = Path("src/routes.json")
    with open(routes_path, "r", encoding="utf-8") as f:
        routes = json.load(f)

    collector = FlightCollector()
    flights = collector.search_flights(routes)

    for flight in flights:
        print(f"✅ Encontrado: {flight['route']} ({flight['airline']}) por R$ {flight['price']:.2f}")
        send_discord_alert(flight)
        print("📨 Alerta enviado para o Discord!")


if __name__ == "__main__":
    run()