# Module for form stage
from ..pipeline.stage import Stage
from ..generators.form_generator import FormGenerator
from ....decision.models.baselines.random_policy import RandomPolicy


class FormStage(Stage):
    def __init__(self, constraints=None, scorers=None, model=None):
        super().__init__(
            constraints=constraints or [],
            scorers=scorers or [],
            model=model or RandomPolicy(),
        )

    def propose(self, ctx):
        generator = FormGenerator()
        return generator.propose()
