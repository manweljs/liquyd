from liquyd import BaseDocument, Property


class PlaygroundLog(BaseDocument):
    id = Property(str, primary_key=True)
    project_name = Property(str)
    endpoint_path = Property(str)
    status_code = Property(int, nullable=True)
    method = Property(str, nullable=True)

    class Meta:
        index = "liquyd_playground_logs"
