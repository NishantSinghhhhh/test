let currentQuestionIndex = 0;
let questions = [];
let userAnswers = {}; 
let hasAnswered = false; 

const quizContainer = document.getElementById('quiz-container');
const questionElement = document.getElementById('question');
const optionsElement = document.getElementById('options');
const prevBtn = document.getElementById('prev-btn');
const nextBtn = document.getElementById('next-btn');

async function fetchingQuestion() {
    try {
        const response = await fetch('https://opentdb.com/api.php?amount=50&type=multiple');
        const data = await response.json();

        questions = data.results;
        displayQuestion();
    } catch (error) {
        console.log('Error Fetching Question: ', error);
    }
}

function displayQuestion() {
    const question = questions[currentQuestionIndex];
    questionElement.textContent = question.question;
    
    const allOptions = [];
    for (let i = 0; i < question.incorrect_answers.length; i++) {
        allOptions.push(question.incorrect_answers[i]);
    }
    allOptions.push(question.correct_answer);
    
    optionsElement.innerHTML = allOptions.sort(() => Math.random() - 0.5).map((option) =>
        `<div class='option' onclick="selectOption('${option}')">${option}</div>`
    ).join('');

    prevBtn.disabled = currentQuestionIndex === 0;
    nextBtn.disabled = !hasAnswered;

    if (userAnswers[currentQuestionIndex]) {
        updateOptionStyles();
    }
}

function selectOption(selectedOption) {
    const correctAnswer = questions[currentQuestionIndex].correct_answer;
    let isCorrect = selectedOption === correctAnswer;
    userAnswers[currentQuestionIndex] = {
        answer: selectedOption,
        correct: isCorrect
    };

    updateOptionStyles();

    localStorage.setItem('userAnswers', JSON.stringify(userAnswers));

    hasAnswered = true;
    nextBtn.disabled = false;
}

function updateOptionStyles() {
    const options = document.querySelectorAll('.option');
    options.forEach(optionElement => {
        const optionText = optionElement.textContent;
        const userAnswer = userAnswers[currentQuestionIndex];
        if (userAnswer) {
            if (userAnswer.answer === optionText) {
                optionElement.classList.add(userAnswer.correct ? 'correct' : 'incorrect');
            } else if (questions[currentQuestionIndex].correct_answer === optionText) {
                optionElement.classList.add('correct');
            }
        }
    });
}

prevBtn.addEventListener('click', () => {
    if (currentQuestionIndex > 0) {
        currentQuestionIndex--;
        displayQuestion();
        hasAnswered = false; 
        nextBtn.disabled = true; 
    }
});

nextBtn.addEventListener('click', () => {
    if (currentQuestionIndex < questions.length - 1 && hasAnswered) {
        currentQuestionIndex++;
        displayQuestion();
        hasAnswered = false; 
        nextBtn.disabled = true; 
    } else if (currentQuestionIndex === questions.length - 1 && hasAnswered) {
        alert('Quiz Completed');
    }
});

fetchingQuestion();
