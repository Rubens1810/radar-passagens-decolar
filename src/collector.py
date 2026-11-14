import os
import httpx


class FlightCollector:
    def __init__(self):
        self.api_key = os.getenv("SERPAPI_KEY")
        self.base_url = "https://serpapi.com/search.json"

    def search_flights(self, routes: list[dict]) -> list[dict]:
        if not self.api_key:
            raise ValueError("SERPAPI_KEY não encontrada no arquivo .env")

        results = []

        for route in routes:
            origin = route["origin"].upper()
            destination = route["destination"].upper()
            departure_date = route["departure_date"]

            print(f"🔎 Consultando Google Flights: {origin} -> {destination} ({departure_date})...")

            params = {
                "engine": "google_flights",
                "departure_id": origin,
                "arrival_id": destination,
                "outbound_date": departure_date,
                "type": "2",  # 2 = Somente ida (One way)
                "currency": "BRL",
                "hl": "pt-br",
                "gl": "br",
                "api_key": self.api_key,
            }

            try:
                response = httpx.get(self.base_url, params=params, timeout=25.0)
                response.raise_for_status()
                data = response.json()

                # O Google Flights divide entre 'best_flights' e 'other_flights'
                all_flights = data.get("best_flights", []) + data.get("other_flights", [])

                if not all_flights:
                    error_msg = data.get("error", "Sem detalhe adicional da API")
                    print(f"⚠️ Nenhum voo encontrado para {origin} -> {destination} em {departure_date}. ({error_msg})")
                    continue

                # Filtra ofertas que possuem preço e pega a mais barata
                priced_flights = [f for f in all_flights if "price" in f]
                cheapest = min(priced_flights, key=lambda x: float(x["price"]))

                cheapest_price = float(cheapest["price"])
                airline = cheapest["flights"][0].get("airline", "Companhia não informada")
                google_flights_url = data.get("search_metadata", {}).get(
                    "google_flights_url",
                    f"https://www.google.com/travel/flights?q=Flights%20to%20{destination}%20from%20{origin}%20on%20{departure_date}",
                )

                results.append(
                    {
                        "route": f"{origin} -> {destination}",
                        "departure_date": departure_date,
                        "airline": airline,
                        "price": cheapest_price,
                        "currency": "BRL",
                        "url": google_flights_url,
                    }
                )

            except httpx.HTTPStatusError as e:
                print(f"⚠️ Erro HTTP na API para {origin}->{destination}: {e.response.text}")
            except Exception as e:
                print(f"⚠️ Erro inesperado em {origin}->{destination}: {e}")

        return results