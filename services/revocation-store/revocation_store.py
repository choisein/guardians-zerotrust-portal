from flask import Flask, request, jsonify
import os

app = Flask(__name__)

REVOCATION_DIR = "/app/revoked"
os.makedirs(REVOCATION_DIR, exist_ok=True)


@app.route("/revoke", methods=["POST"])
def revoke():
    data = request.get_json()

    spiffe_id = data.get("spiffe_id", "")
    service_name = spiffe_id.split("/")[-1]

    revoked_path = os.path.join(
        REVOCATION_DIR,
        f"{service_name}.revoked"
    )

    with open(revoked_path, "w") as f:
        f.write("revoked")

    print(f"[REVOCATION] {service_name} revoked")

    return jsonify({
        "status": "revoked",
        "service": service_name
    })


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6000)