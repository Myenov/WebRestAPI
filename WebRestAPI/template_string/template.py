class Template:
    def __init__(self,template: str, symbol: str = "$"):
        self.template: str = template
        self.symbol: str = symbol

    def connect(self, variable: dict[str , str | int | float | bool | dict | list ]) -> str | None:
        try:
            for key , value in variable.items():
                self.template = self.template.replace(self.symbol + key , str(value))
            return self.template
        except Exception as e:
            print(e)

    def __str__(self):
        return self.template




