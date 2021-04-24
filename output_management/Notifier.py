from __future__ import annotations

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from operator import attrgetter

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import List
    from AgentPool import AgentPool


class Notifier:
    def __init__(self, email: str, password: str, recipients: List[str], id: str) -> None:
        self.email = email
        self.password = password
        self.recipients = recipients
        self.id = id

    def sendEmail(self, subject: str, content: str) -> None:
        port = 465
        context = ssl.create_default_context()
        message = MIMEMultipart("alternative")
        message["Subject"] = f"ASP VM: {self.id} {subject}"
        message["From"] = self.email

        message.attach(MIMEText(content, "plain"))
        with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
            server.login(self.email, self.password)
            for recipient in self.recipients:
                message['To'] = recipient
                server.sendmail(self.email, recipient, message.as_string())

    def run(self, agentPools: List[AgentPool], generationRuntimes: List[float], episodeRuntimes: List[float], totalGenerations: int):
        genTime = generationRuntimes[-1]
        averageGenTime = sum(generationRuntimes) / len(generationRuntimes)
        generations = len(generationRuntimes)
        averageEpisodeTime = sum(episodeRuntimes) / len(episodeRuntimes)
        episodes = len(episodeRuntimes)

        # Create new output file and add generation runtime information
        message = ""
        message += f"Generation {generations} Stats\n\n"
        message += f"Generation runtime: {genTime}\n"
        message += f"Average generation runtime: {averageGenTime}\n"
        message += f"Average episode runtime: {averageEpisodeTime}\n"
        message += f"Episodes: {episodes}\n"
        message += "\n---------------------------\n\n"
        message += "Best Individuals per Agent Pool\n\n"

        for ap in agentPools:
            actionSet = ""
            for a in ap.getActionSet()[:-1]:
                actionSet += f"{a}, "
            actionSet += ap.getActionSet()[-1]

            message += f"ID: {ap.getID()}\n"
            message += f"Action set: {', '.join(ap.getActionSet())}\n"

            individuals = ap.getIndividualsSet()
            topIndividual = min(individuals, key=attrgetter('fitness'))
            message += f"Top individual fitness: {topIndividual.getFitness()}"

            nonZeroRules = {
                "RS": [str(r) for r in topIndividual.getRS() if r.getWeight() != 0],
                "RSint": [str(r) for r in topIndividual.getRSint() if r.getWeight() != 0],
            }
            for ruleSet in nonZeroRules:
                if nonZeroRules[ruleSet] == []:
                    continue
                message += f"\n\n{ruleSet}\n"
                for rule in nonZeroRules[ruleSet]:
                    message += rule
            message += "\n\n*************************\n\n"

        self.sendEmail(f"Gen {generations} of {totalGenerations} complete!", message)
