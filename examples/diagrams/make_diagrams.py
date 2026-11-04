#!/usr/bin/env python3
"""Generate the example draw.io diagrams, one function each.

Run from the repository root: python3 examples/diagrams/make_diagrams.py
"""

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIB = HERE.parent.parent / "skills" / "diagram-lint" / "scripts" / "drawio_lib.py"

spec = importlib.util.spec_from_file_location("drawio_lib", LIB)
assert spec is not None and spec.loader is not None
lib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lib)

ICON = 78
BELOW = "verticalLabelPosition=bottom;verticalAlign=top;"
# Moves a caption off the side that a vertical line leaves from.
ABOVE = "verticalLabelPosition=top;verticalAlign=bottom;"

AWS_ICON = (
    "outlineConnect=0;fontColor=#232F3E;fillColor={colour};strokeColor=#ffffff;dashed=0;"
    "align=center;html=1;fontSize=12;aspect=fixed;shape=mxgraph.aws4.resourceIcon;"
    "resIcon=mxgraph.aws4.{name};{caption}"
)
AWS_USERS = (
    "outlineConnect=0;fontColor=#232F3E;fillColor=#232F3D;strokeColor=none;dashed=0;"
    "align=center;html=1;fontSize=12;aspect=fixed;pointerEvents=1;"
    f"shape=mxgraph.aws4.users;{BELOW}"
)
# fillColor=none marks a boundary, which check_layout.py does not treat as an obstacle.
AWS_GROUP = (
    "outlineConnect=0;html=1;whiteSpace=wrap;fontSize=12;fontStyle=1;collapsible=0;"
    "shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.{icon};strokeColor={colour};fillColor=none;"
    "verticalAlign=top;align=left;spacingLeft=30;fontColor={colour};dashed=0;"
)
K8S_ICON = (
    "html=1;dashed=0;fillColor=#326CE5;strokeColor=#ffffff;align=center;fontSize=12;"
    "fontColor=#1F2937;aspect=fixed;shape=mxgraph.kubernetes.icon;prIcon={name};{caption}"
)
K8S_BOUND = (
    "rounded=1;arcSize=2;html=1;whiteSpace=wrap;fillColor=none;strokeColor=#326CE5;{dash}"
    "verticalAlign=top;align=left;spacingLeft=10;spacingTop=4;fontStyle=1;fontSize=13;"
    "fontColor=#326CE5;"
)
AZURE_ICON = (
    "aspect=fixed;html=1;points=[];align=center;image;fontSize=12;fontColor=#1F2937;"
    "image=img/lib/azure2/{path}.svg;{caption}"
)
AZURE_BOUND = (
    "rounded=1;arcSize=2;html=1;whiteSpace=wrap;fillColor=none;strokeColor=#0078D4;dashed=1;"
    "verticalAlign=top;align=left;spacingLeft=10;spacingTop=4;fontStyle=1;fontSize=13;"
    "fontColor=#0078D4;"
)


def caption(title: str, detail: str = "") -> str:
    """A two-line icon caption: bold product name, plain role."""
    return f"<b>{title}</b><br/>{detail}" if detail else f"<b>{title}</b>"


def aws_web_app() -> None:
    d = lib.Doc("aws-web-app", width=1280, height=740)

    def icon(cap: str, x: float, y: float, name: str, colour: str, where: str = BELOW) -> str:
        style = AWS_ICON.format(colour=colour, name=name, caption=where)
        return d.node(cap, x, y, ICON, ICON, style)

    # Boundaries go first so that they draw behind everything else.
    d.node(
        "AWS Cloud", 200, 30, 1050, 680,
        AWS_GROUP.format(icon="group_aws_cloud_alt", colour="#232F3E"),
    )
    d.node(
        "VPC", 440, 80, 790, 450,
        AWS_GROUP.format(icon="group_vpc2", colour="#8C4FFF"),
    )
    d.node(
        "Public subnet", 470, 130, 200, 380,
        AWS_GROUP.format(icon="group_security_group", colour="#248814"),
    )
    d.node(
        "Private subnet", 700, 130, 510, 380,
        AWS_GROUP.format(icon="group_security_group", colour="#147EBA"),
    )

    users = d.node(caption("Users"), 40, 281, ICON, ICON, AWS_USERS)
    cdn = icon(caption("CloudFront", "CDN"), 240, 281, "cloudfront", "#8C4FFF", ABOVE)
    assets = icon(caption("S3", "Static assets"), 240, 575, "s3", "#7AA116")
    alb = icon(
        caption("Load balancer", "Application"),
        531, 281, "application_load_balancer", "#8C4FFF", ABOVE,
    )
    api = icon(caption("Fargate", "API service"), 790, 281, "fargate", "#ED7100", ABOVE)
    db = icon(caption("Aurora", "PostgreSQL"), 1090, 180, "aurora", "#C925D1", ABOVE)
    cache = icon(caption("ElastiCache", "Sessions"), 1090, 382, "elasticache", "#C925D1")
    queue = icon(caption("SQS", "Order events"), 790, 575, "sqs", "#E7157B")
    worker = icon(caption("Lambda", "Receipt worker"), 1090, 575, "lambda", "#ED7100")

    d.hlink(users, cdn, "HTTPS", label_pos=-0.48)
    d.vlink(cdn, assets, "Static paths")
    d.hlink(cdn, alb, "/api/*", label_pos=-0.42)
    d.hlink(alb, api, "HTTP", label_pos=0.5)
    d.elbow(api, db, "SQL", 1129, 306, first="h")
    d.elbow(api, cache, "Cache", 1129, 334, first="h")
    d.vlink(api, queue, "Publishes")
    d.hlink(queue, worker, "Triggers")
    d.write(str(HERE / "aws-web-app.drawio"))


def c4_container() -> None:
    d = lib.Doc("c4-container", width=1120, height=640)
    d.node(
        lib.label("Online shop", "Software system"), 60, 180, 660, 420, lib.S_BOUND,
    )

    customer = d.person(
        lib.label("Customer", "Person", "Browses and buys"), 110, 0, 180, 160,
    )
    web = d.node(
        lib.label("Web app", "React", "Catalogue and checkout"),
        100, 260, 200, 84, lib.S_CONT,
    )
    api = d.node(
        lib.label("API", "Python, FastAPI", "Orders and payments"),
        480, 260, 200, 84, lib.S_CONT,
    )
    db = d.node(
        lib.label("Orders database", "PostgreSQL", "Orders and stock"),
        100, 480, 200, 100, lib.S_DB,
    )
    worker = d.node(
        lib.label("Worker", "Python, Celery", "Sends receipts"),
        480, 488, 200, 84, lib.S_CONT,
    )
    payments = d.node(
        lib.label("Payment provider", "External system", "Takes card payments"),
        900, 260, 200, 84, lib.S_EXT,
    )
    email = d.node(
        lib.label("Email service", "External system", "Delivers receipts"),
        900, 488, 200, 84, lib.S_EXT,
    )

    d.vlink(customer, web, "Checks out", lib.S_EDGE_HL, label_pos=0.3)
    d.hlink(web, api, "JSON over HTTPS", lib.S_EDGE_HL, lane=302)
    d.hlink(api, payments, "Charges card", lib.S_EDGE_HL, label_pos=0.2)
    d.vlink(api, worker, "Order placed event", lib.S_EDGE_DASH)
    d.hlink(worker, email, "Sends receipt", lib.S_EDGE_DASH, label_pos=0.2)
    d.route(api, db, "Writes order", [(390, 330), (390, 510)])
    d.hlink(worker, db, "Reads order", lane=550)
    d.write(str(HERE / "c4-container.drawio"))


def kubernetes_platform() -> None:
    d = lib.Doc("kubernetes-platform", width=1360, height=700)

    def icon(cap: str, x: float, y: float, name: str, where: str = ABOVE) -> str:
        return d.node(cap, x, y, ICON, ICON, K8S_ICON.format(name=name, caption=where))

    d.node("Cluster", 190, 10, 1140, 670, K8S_BOUND.format(dash=""))
    d.node("Namespace: shop", 215, 45, 1090, 610, K8S_BOUND.format(dash="dashed=1;"))

    users = icon(caption("Users"), 40, 220, "user", BELOW)
    ingress = icon(caption("Ingress", "nginx"), 260, 220, "ing", BELOW)
    web_svc = icon(caption("Service", "frontend"), 500, 110, "svc")
    web = icon(caption("Deployment", "frontend, 3 replicas"), 740, 110, "deploy")
    api_svc = icon(caption("Service", "api"), 500, 330, "svc")
    api = icon(caption("Deployment", "api, 4 replicas"), 740, 330, "deploy")
    db = icon(caption("StatefulSet", "postgres"), 980, 330, "sts")
    pvc = icon(caption("PVC", "100 GiB"), 1200, 330, "pvc")
    config = icon(caption("ConfigMap", "app-config"), 620, 530, "cm", BELOW)
    autoscaler = icon(caption("HPA", "CPU at 70%"), 740, 530, "hpa", BELOW)
    secret = icon(caption("Secret", "db-credentials"), 860, 530, "secret", BELOW)

    d.hlink(users, ingress, "HTTPS", label_pos=-0.35)
    d.route(ingress, web_svc, "/", [(410, 245), (410, 149)])
    d.route(ingress, api_svc, "/api", [(410, 273), (410, 369)])
    d.hlink(web_svc, web, "Routes to")
    d.hlink(api_svc, api, "Routes to")
    d.hlink(api, db, "SQL")
    d.hlink(db, pvc, "Mounts")
    dash = lib.S_EDGE_DASH
    d.elbow(config, api, "Env", 659, 390, dash, first="v")
    d.vlink(autoscaler, api, "Scales", dash)
    d.elbow(secret, api, "Password", 899, 390, dash, first="v")
    d.write(str(HERE / "kubernetes-platform.drawio"))


def azure_telemetry() -> None:
    d = lib.Doc("azure-telemetry", width=1240, height=580)

    def icon(cap: str, x: float, y: float, path: str, where: str = ABOVE) -> str:
        return d.node(cap, x, y, ICON, ICON, AZURE_ICON.format(path=path, caption=where))

    d.node("Resource group: telemetry", 230, 40, 960, 510, AZURE_BOUND)

    sensors = d.node(
        lib.label("Factory sensors", "External", "Publish readings"),
        20, 136, 150, 78, lib.S_EXT,
    )
    hub = icon(caption("Event Hubs", "Ingest"), 280, 136, "analytics/Event_Hubs")
    stream = icon(
        caption("Stream Analytics", "Windowed aggregates"),
        530, 136, "analytics/Stream_Analytics_Jobs",
    )
    store = icon(
        caption("Cosmos DB", "Latest readings"), 790, 136, "databases/Azure_Cosmos_DB",
    )
    alerts = icon(caption("Functions", "Alerting API"), 1050, 136, "compute/Function_Apps")
    lake = icon(
        caption("Data Lake", "Raw events"), 530, 400, "storage/Data_Lake_Storage_Gen1", BELOW,
    )
    warehouse = icon(
        caption("Synapse", "Warehouse"), 790, 400, "analytics/Azure_Synapse_Analytics", BELOW,
    )

    d.hlink(sensors, hub, "MQTT", lane=175, label_pos=-0.4)
    d.hlink(hub, stream, "Events")
    d.hlink(stream, store, "Aggregates")
    d.hlink(store, alerts, "Reads")
    d.elbow(hub, lake, "Capture", 319, 439, first="v", label_pos=0.5)
    d.hlink(lake, warehouse, "Batch load")
    d.vlink(store, warehouse, "Synapse Link", label_pos=0.45)
    # Emitted after the Synapse Link, because draw.io draws a jump only on the later edge.
    d.route(
        stream, alerts, "Anomalies", [(569, 300), (1089, 300)],
        lib.S_EDGE_HL, label_pos=-0.35, jump=True,
    )
    d.write(str(HERE / "azure-telemetry.drawio"))


def lint_demo(name: str, fixed: bool) -> None:
    """The same content twice: once with the faults the check catches, once with them fixed."""
    d = lib.Doc(name, width=880, height=400)
    queue_x, db_x = (700, 370) if fixed else (370, 700)

    gateway = d.node(lib.label("Gateway", "Envoy"), 40, 120, 150, 70, lib.S_CONT)
    orders = d.node(lib.label("Orders", "Go"), 370, 120, 150, 70, lib.S_CONT)
    billing = d.node(lib.label("Billing", "Go"), 700, 120, 150, 70, lib.S_CONT)
    queue = d.node(lib.label("Queue", "RabbitMQ"), queue_x, 300, 150, 70, lib.S_CONT)
    db = d.node(lib.label("Database", "PostgreSQL"), db_x, 300, 150, 70, lib.S_DB)

    if fixed:
        d.hlink(gateway, orders, "Orders")
        d.route(gateway, billing, "Invoices", [(115, 60), (775, 60)])
        d.vlink(orders, db, "Writes")
        d.vlink(billing, queue, "Publishes")
    else:
        d.hlink(gateway, orders, "Orders", lane=172)
        d.hlink(gateway, billing, "Invoices", lane=138, label_pos=-0.65)
        d.route(orders, db, "Writes", [(445, 235), (775, 235)])
        d.route(billing, queue, "Publishes", [(740, 235), (740, 262), (445, 262)])
    d.write(str(HERE / f"{name}.drawio"))


if __name__ == "__main__":
    aws_web_app()
    c4_container()
    kubernetes_platform()
    azure_telemetry()
    lint_demo("lint-before", fixed=False)
    lint_demo("lint-after", fixed=True)
