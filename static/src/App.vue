<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const questions = ref({
  name: '',
  answer: 0,
  options: []
})
const selected = ref(null)
const hasPhotos = ref(false)

const fetchPhotosCount = async () => {
  try {
    const response = await axios.get('/api/photos/count')
    hasPhotos.value = Number(response.data?.count || 0) > 0
  } catch (error) {
    console.error(error)
    hasPhotos.value = false
  }
}

const fetchQuestion = async (sourceLabel) => {
  try {
	// Randomly call year or city question in future
    const apiUrl = '/api/year'
    console.log(`fetching question (${sourceLabel}):`, apiUrl)
    const response = await axios.get(apiUrl)
    const responseData = response.data
	// year options generation
	const currentYear = new Date().getFullYear()
    const minYear = responseData.year - 4
    const maxYear = responseData.year + 4
    const candidates = Array.from({ length: maxYear - minYear + 1 }, (_, i) => minYear + i)
      .filter((year) => year !== responseData.year && year < currentYear)
	  .sort(() => Math.random() - 0.5).slice(0, 3)

    questions.value.name = responseData.name
    questions.value.answer = responseData.year
	questions.value.options = [responseData.year, ...candidates].sort(() => Math.random() - 0.5)
	
    console.log(`questions updated (${sourceLabel}):`, { ...questions.value })
  } catch (error) {
    console.error(error)
  }
}

onMounted(async () => {
  await fetchPhotosCount()
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
		<div v-if="!hasPhotos" class="empty-state">
			<span class="empty-message">No hay fotos disponibles. Por favor, sube algunas fotos para comenzar el concurso.</span>
		</div>
		<div v-else class="mainElement">
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
						correct: selected != null && String(option) === String(questions.answer),
						wrong: selected != null  && String(option) !== String(questions.answer)&& String(selected) === String(option),
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
			<img :src="'/fotos/' + questions.name" />
		</div>	
	</div>
		
	</main>
</template>
