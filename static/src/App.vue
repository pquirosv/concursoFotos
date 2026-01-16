<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const questions = ref({
  name: '',
  answer: 0,
  options: []
})
const selected = ref(null)

const fetchQuestion = async (sourceLabel) => {
  try {
    const apiUrl = '/api/year'
    console.log(`fetching question (${sourceLabel}):`, apiUrl)
    const response = await axios.get(apiUrl)
    const responseData = response.data

    questions.value.name = responseData.name
    questions.value.answer = responseData.year
    questions.value.options = responseData.yearOptions.sort(() => Math.random() - 0.5)
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
  await fetchQuestion('newQuestion')
}

const SetAnswer = (e) => {
  console.log('option clicked:', e?.target?.value)
}
</script>


<template>
	<main class="app">
		<h1>Concurso</h1>
		<div class="mainElement">
		<div class="quiz">
			<div class="quiz-info">
				<span class="question">¿De que año es esta foto?</span>
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
			 <div class="buttonContainer">
			<button class="slctButton"
				@click="newQuestion" 
				:disabled="selected === null">
				{{ 
						selected == null
							? 'Selecciona una Opción'
							: 'Siguiente pregunta'
				}}
			</button>
			</div>
		</div>
		<div class="foto">
			<img :src="'/fotos/' + questions.name" width="300" height="300"/>
		</div>	
	</div>
		
	</main>
</template>
