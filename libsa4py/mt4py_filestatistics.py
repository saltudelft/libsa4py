import json
from enum import Enum
import dictfier


class predictionElement:
    def __init__(self, name, pe_type, match_case, original_type, line_number):
        self.name = name
        self.type = pe_type
        self.match_case = match_case
        self.original_type = original_type
        self.predicted_type = ""
        self.line_number = line_number


class fileStatistics:
    def __init__(self, filename):
        self.filename = filename
        self.predictionElements: list[predictionElement] = []

    def addPredictionElement(self, prediction_element: predictionElement):
        self.predictionElements.append(prediction_element)

    def concatPredictionElements(self, prediction_elements: list[predictionElement]):
        self.predictionElements.extend(prediction_elements)

    def toJSON(self):
        query = [
            "filename",
            {
                "predictionElements": [
                    [
                        "name",
                        "type",
                        "match_case",
                        "original_type",
                        "predicted_type",
                        "line_number",
                    ]
                ]
            },
        ]
        return json.dumps(self, default=lambda o: dictfier.dictfy(o, query), indent=4)
