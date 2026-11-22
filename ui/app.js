const habitsUrl = window.APP_CONFIG.habitsUrl;
const completionsUrl = window.APP_CONFIG.completionsUrl;
const form = document.querySelector("#habit-form");
const nameInput = document.querySelector("#habit-name");
const habitList = document.querySelector("#habits");
const statusElement = document.querySelector("#status");

async function readJson(response) {
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(body.error || `Request failed with status ${response.status}`);
  }
  return body;
}

async function loadHabits() {
  try {
    statusElement.textContent = "";
    const habits = await readJson(await fetch(`${habitsUrl}/habits`));
    habitList.replaceChildren();

    for (const habit of habits) {
      const item = document.createElement("li");
      item.textContent = habit.name;

      const completeButton = document.createElement("button");
      completeButton.type = "button";
      completeButton.textContent = "Complete today";
      completeButton.addEventListener("click", async () => {
        try {
          await readJson(await fetch(
            `${completionsUrl}/habits/${habit.id}/completions`,
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: "{}"
            }
          ));
          statusElement.textContent = `Completed ${habit.name}`;
        } catch (error) {
          statusElement.textContent = error.message;
        }
      });

      item.append(" ", completeButton);
      habitList.append(item);
    }
  } catch (error) {
    statusElement.textContent = error.message;
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await readJson(await fetch(`${habitsUrl}/habits`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: nameInput.value })
    }));
    nameInput.value = "";
    await loadHabits();
  } catch (error) {
    statusElement.textContent = error.message;
  }
});

loadHabits();
