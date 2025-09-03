import json

# -------------------------------
# Fake Tool Implementations
# -------------------------------
class CalendarAPI:
    def check_availability(self, person):
        slots = {
            "user": ["Wed 10AM", "Thu 11AM"],
            "Priya": ["Thu 11AM", "Fri 2PM"]
        }
        return slots.get(person, [])

class EmailAPI:
    def draft_email(self, to, subject, body):
        return f"Drafted email to {to} with subject '{subject}': {body}"

# -------------------------------
# Mock GPT (Stateful Fake)
# -------------------------------
class FakeGPT:
    def __init__(self):
        self.step = 0

    def run(self, task):
        self.step += 1

        if self.step == 1:
            return json.dumps({
                "thought": "I need to start by checking calendars.",
                "plan": "Step 1: Call CalendarAPI for user and Priya.",
                "action": "CalendarAPI.check_availability",
                "observation": "None yet.",
                "final_answer": "Checking availability..."
            })
        elif self.step == 2:
            return json.dumps({
                "thought": "Now I have both calendars. I should find a common slot.",
                "plan": "Compare availability of user and Priya.",
                "action": "none",
                "observation": "User: Wed 10AM, Thu 11AM | Priya: Thu 11AM, Fri 2PM",
                "final_answer": "Both are free on Thu 11AM. Should I draft an email?"
            })
        elif self.step == 3:
            return json.dumps({
                "thought": "I should draft a confirmation email to Priya.",
                "plan": "Use EmailAPI to create a draft.",
                "action": "EmailAPI.draft_email",
                "observation": "None yet.",
                "final_answer": "Drafting the email now."
            })
        else:
            return json.dumps({
                "thought": "The task is complete.",
                "plan": "No further action needed.",
                "action": "none",
                "observation": "All done.",
                "final_answer": "Email drafted successfully and meeting scheduled."
            })

# -------------------------------
# Agent Loop
# -------------------------------
class AIAgent:
    def __init__(self):
        self.calendar = CalendarAPI()
        self.email = EmailAPI()
        self.gpt = FakeGPT()

    def run(self, task):
        print(f"User task: {task}\n")

        step = 0
        done = False
        while not done and step < 5:  # safety limit
            step += 1
            print(f"--- Step {step} ---")

            # 1. Get GPT reasoning
            response = self.gpt.run(task)
            parsed = json.loads(response)

            # 2. Print reasoning
            print("Thought:", parsed["thought"])
            print("Plan:", parsed["plan"])
            print("Action:", parsed["action"])

            # 3. Execute fake tool
            if parsed["action"] == "CalendarAPI.check_availability":
                obs_user = self.calendar.check_availability("user")
                obs_priya = self.calendar.check_availability("Priya")
                parsed["observation"] = f"User: {obs_user} | Priya: {obs_priya}"

            elif parsed["action"] == "EmailAPI.draft_email":
                email = self.email.draft_email(
                    "Priya",
                    "Meeting Confirmation",
                    "Hi Priya, confirming our meeting on Thu 11AM."
                )
                parsed["observation"] = email

            # 4. Show observation + answer
            print("Observation:", parsed["observation"])
            print("Final Answer:", parsed["final_answer"], "\n")

            # Stop when final confirmation is reached
            if "successfully" in parsed["final_answer"].lower():
                done = True

# -------------------------------
# Run Example
# -------------------------------
agent = AIAgent()
agent.run("Schedule a meeting with Priya next week and send her a confirmation email.")
