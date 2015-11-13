from rally.common import objects
from rally.deployment import engine




@engine.configure(name="MessagingEngine")
class MessagingEngine(engine.Engine):
    def deploy(self):
        url = self.config.get("url")
        return {"admin": objects.Endpoint(url, "-", "-")}

    def cleanup(self):
        pass

    def validate(self):
        # TODO(yportnova): check rabbit available"
        pass