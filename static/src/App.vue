<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const questions = ref({
  name: '',
  answer: 0,
  options: []
})
const selected = ref(null)
const yearOrCity = ref(Math.random() < 0.5)

const fetchQuestion = async (sourceLabel) => {
  try {
    const apiUrl = yearOrCity.value ? 'http://localhost:3000/api/year' : 'http://localhost:3000/api/city'
    console.log(`fetching question (${sourceLabel}):`, apiUrl)
    const response = await axios.get(apiUrl)
    const responseData = response.data

    questions.value.name = responseData.name
    questions.value.answer = yearOrCity.value ? responseData.year : responseData.city
    questions.value.options = yearOrCity.value
      ? responseData.yearOptions.sort(() => Math.random() - 0.5)
      : responseData.cityOptions.sort(() => Math.random() - 0.5)
    console.log(`questions updated (${sourceLabel}):`, { ...questions.value })
  } catch (error) {
    console.error(error)
  }
}

onMounted(async () => {
  await fetchQuestion('onMounted')
})

const newQuestion = async () => {
  selected.value = null
  yearOrCity.value = !yearOrCity.value
  await fetchQuestion('newQuestion')
}

const SetAnswer = (e) => {
  console.log('option clicked:', e?.target?.value)
}
</script>


<template>
	<main class="app">
		<h1>¡Feliz cumpleaños!</h1>
		<div class="mainElement">
		<section class="quiz">
			<div class="quiz-info">
				<span class="question" v-if="yearOrCity">
					¿De que año es esta foto?</span>
					<span class="question" v-else>
					¿En que ciudad se hizo esta foto?</span>
			</div>
			
			<div class="options">
				<label  
					v-for="(option, index) in questions.options" 
					:for="'option' + index" 
					:class="{
						option: true,
						correct: selected != null && String(selected) === String(option) && String(option) === String(questions.answer),
						wrong: selected != null && String(selected) === String(option) && String(option) !== String(questions.answer),
						disabled: selected != null
					}">
					<input 
						type="radio" 
						:id="'option' + index" 
						:name="option" 
						:value="option" 
						v-model="selected" 
						:disabled="selected !== null"
						@change="SetAnswer" 
					/>
					<span>{{ option }} </span>
				</label>
			</div>
			<!-- en Click: Volver a llamar a la api para que me de una nueva pregunta-->
			<button 
				@click="newQuestion" 
				:disabled="selected === null">
				{{ 
						selected == null
							? 'Selecciona una Opción'
							: 'Siguiente pregunta'
				}}
			</button>
		</section>
		<div class="foto">
			<img :src="'/fotos/' + questions.name" width="300" height="300"/>
		</div>	
	</div>
		
	</main>
</template>

<style>
* {
	margin: 0;
	padding: 0;
	box-sizing: border-box;
	font-family: 'Montserrat', sans-serif;
}

body {
	background-color: #271c36;
	color: #FFF;
}

.app {
	display: flex;
	flex-direction: column;
	align-items: center;
	padding: 2rem;
	height: 100vh;
}

h1 {
	font-size: 2rem;
	margin-bottom: 2rem;
}

.foto {
	padding: 2rem;
}

.mainElement {
	display: flex;
	flex-direction: row;
}

.quiz {
	background-color: #382a4b;
	padding: 2rem;
	width: 100%;
	max-width: 640px;
}

.quiz-info {
	display: flex;
	justify-content: space-between;
	margin-bottom: 1rem;
}

.quiz-info .question {
	color: #8F8F8F;
	font-size: 1.25rem;
}

.quiz-info.score {
	color: #FFF;
	font-size: 1.25rem;
}

.options {
	margin-bottom: 1rem;
}

.option.correct {
	background-color: #2cce7d;
}

.option.wrong {
	background-color: #ff5a5f;
}

.option {
	padding: 1rem;
	display: block;
	background-color: #271c36;
	margin-bottom: 0.5rem;
	border-radius: 0.5rem;
	cursor: pointer;
}

.option:hover {
	background-color: #2d213f;
}

.option:last-of-type {
	margin-bottom: 0;
}

.option.disabled {
	opacity: 0.5;
}

.option input {
	display: none;
}

button {
	appearance: none;
	outline: none;
	border: none;
	cursor: pointer;
	padding: 0.5rem 1rem;
	background-color: #2cce7d;
	color: #2d213f;
	font-weight: 700;
	text-transform: uppercase;
	font-size: 1.2rem;
	border-radius: 0.5rem;
}

button:disabled {
	opacity: 0.5;
}

h2 {
	font-size: 2rem;
	margin-bottom: 2rem;
	text-align: center;
}

p {
	color: #8F8F8F;
	font-size: 1.5rem;
	text-align: center;
}
</style>
