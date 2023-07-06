function updateElapsedTime(startTime) {
    const elapsedTimeElement = document.getElementById("elapsed-time-value");
    const currentTime = new Date();
    const elapsedTime = Math.floor((currentTime - startTime) / 1000);
    elapsedTimeElement.textContent = elapsedTime;
  }
  
  const generateBtn = document.getElementById("generate-btn");
  if (generateBtn) {
    generateBtn.addEventListener("click", (event) => {
      event.preventDefault();
  
      const newsInput = document.getElementById("news-input");
      const newsOutput = document.getElementById("news-output");
      const loader = document.getElementById("loader");
      const elapsedTimeContainer = document.getElementById("elapsed-time-container");
  
      if (!newsInput.value) {
        alert("Please enter some news before generating the post.");
        return;
      }
  
      loader.classList.remove("hidden");
      elapsedTimeContainer.classList.remove("hidden");
  
      const startTime = new Date();
      updateElapsedTime(startTime);
  
      const elapsedTimeInterval = setInterval(() => {
        updateElapsedTime(startTime);
      }, 1000);
  
      const formData = new FormData();
      formData.append("news",newsInput.value);
      fetch("/generate", {
        method: "POST",
        body: formData,
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error("Network response was not ok");
          }
          return response.json();
        })
        .then((data) => {
          if (data.error) {
            newsOutput.value = data.error;
          } else {
            newsOutput.value = data.result;
          }
          loader.classList.add("hidden");
          clearInterval(elapsedTimeInterval);
        })
        .catch((error) => {
          console.error("Error:", error);
          loader.classList.add("hidden");
          elapsedTimeContainer.classList.add("hidden");
          clearInterval(elapsedTimeInterval);
        });
      
      });
    }
    
    const regenerateBtn = document.getElementById("regenerate-btn");
    if (regenerateBtn) {
    regenerateBtn.addEventListener("click", () => {
    document.getElementById("news-input").value = "";
    document.getElementById("news-output").value = "";
    generateBtn.click();
    });
    }
  