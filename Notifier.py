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
    def __init__(self, email: str, password: str, recipients: List[str]) -> None:
        self.email = email
        self.password = password
        self.recipients = recipients

    def sendEmail(self, subject: str, content: str) -> None:
        port = 465
        context = ssl.create_default_context()
        message = MIMEMultipart("alternative")
        message["Subject"] = f"ASP VM: {subject}"
        message["From"] = self.email

        message.attach(MIMEText(content, "plain"))
        with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
            server.login(self.email, self.password)
            for recipient in self.recipients:
                message['To'] = recipient
                server.sendmail(self.email, recipient, message.as_string())

    def run(self, agentPools: List[AgentPool], avgGenTime: float, totalGenTime: float, generations: int, totalGenerations: int):
        avgGenRuntime = avgGenTime
        finalGenRuntime = totalGenTime

        # Create new output file and add generation runtime information
        message = ""
        message += f"Generation {generations} Stats\n\n"
        message += f"Generation runtime: {finalGenRuntime}\n"
        message += f"Average Generation runtime: {avgGenRuntime}"
        message += "\n---------------------------\n\n"
        message += "Best Individuals per Agent Pool\n"

        for ap in agentPools:
            actionSet = ""
            for a in ap.getActionSet()[:-1]:
                actionSet += f"{a}, "
            actionSet += ap.getActionSet()[-1]

            message += f"Agent Pool {ap.getID()}\n"
            message += f"This agent pool has an action set of: {', '.join(ap.getActionSet())}\n"

            individuals = ap.getIndividualsSet()
            individuals.sort
            topIndividual = min(individuals, key=attrgetter('fitness'))
            message += f"The top individual has a fitness of {topIndividual.getFitness()}"

            message += "RS:\n"
            for rule in topIndividual.getRS():
                message += str(rule)

            message += "RSint:\n"
            for rule in topIndividual.getRSint():
                message += str(rule)

            message += "RSev:\n"
            for rule in topIndividual.getRSev():
                message += str(rule)

            message += "*******\n"

        self.sendEmail(f"Gen {generations} of {totalGenerations} complete!", message)
