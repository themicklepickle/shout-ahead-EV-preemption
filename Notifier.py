import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from operator import attrgetter


class Notifier:
    def __init__(self, email, password, recipients) -> None:
        self.email = email
        self.password = password
        self.recipients = recipients

    def sendEmail(self, subject, content) -> None:
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

    def run(self, agentPools, avgGenTime, totalGenTime, generations, totalGenerations):
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
            message += f"This agent pool has an action set of: {actionSet}\n"

            individuals = ap.getIndividualsSet()
            individuals.sort
            topIndividual = min(individuals, key=attrgetter('fitness'))
            message += f"The top individual has a fitness of {topIndividual.getFitness()} and its RS and RSint sets contain the following rules (formatted as \"<conditions>, <action>\"):\n\n"

            message += "RS:\n"
            ruleCount = 1
            for rule in topIndividual.getRS():
                cond = ""
                for c in rule.getConditions()[:-1]:
                    cond += f"{c}, "
                cond += rule.getConditions()[-1]

                message += f"RS Rule {ruleCount}: <{cond}> , <{rule.getAction()}> and rule has a weight of {rule.getWeight()}\n\n"
                ruleCount += 1

            message += "RSint:\n"
            ruleCount = 1
            for rule in topIndividual.getRSint():
                cond = ""
                for c in rule.getConditions()[:-1]:
                    cond += f"{c}, "
                cond += rule.getConditions()[-1]

                message += f"RSint Rule {ruleCount}: <{cond}> , <{rule.getAction()}> and rule has a weight of {rule.getWeight()}\n\n"
                ruleCount += 1

            message += "*******\n"

        self.sendEmail(f"Gen {generations} of {totalGenerations} complete!", message)
