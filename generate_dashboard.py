
from models import DataPackage
import jinja2
data_package_file = "data_package.json"

with open(data_package_file, "r") as f:
    data_package = DataPackage.model_validate_json(f.read())

# Set up Jinja2 environment
env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(searchpath="./"),
    autoescape=jinja2.select_autoescape(['html', 'xml'])
)
template = env.get_template("dashboard_tmplate.jinja")

# Render the template with the data package
rendered_html = template.render(date_title="Hello World")
output_file = "rendered_dashboard.html"