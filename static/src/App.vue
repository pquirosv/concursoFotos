<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const questions = ref({
  name: '',
  mode: '',
  answer: 0,
  options: []
})
const selected = ref(null)

const hasPhotos = ref(false)
const hasYearPhoto = ref(false)
const cities = ref([])
const hasInitialized = ref(false)
const questionMode = ref(() => '/api/year')

// Fetch dataset metadata once (photo count, year availability, cities list).
const initDatasetInfo = async () => {
  if (hasInitialized.value) return
  try {
    const response = await axios.get('/api/photos/count')
    hasPhotos.value = Number(response.data?.count || 0) > 0
	//if has photos, check if there are photos with year field and fetch cities
	if (hasPhotos.value) {
		const yearResponse = await axios.get('/api/photos/hasYearPhoto')
		hasYearPhoto.value = yearResponse.data?.hasYearPhoto || false
		const citiesResponse = await axios.get('/api/cities')
		cities.value = citiesResponse.data || []
		setQuestionMode()
	}
    hasInitialized.value = true
  } catch (error) {
    console.error(error)
    hasPhotos.value = false
    hasInitialized.value = true
  }
}

// Determine the question mode based on dataset characteristics.
const setQuestionMode = () => {
	if (hasYearPhoto.value && cities.value.length > 0) {
		questionMode.value = () => (Math.random() < 0.5 ? '/api/year' : '/api/city')
	} else if (!hasYearPhoto.value) {
		questionMode.value = () => '/api/city'
	} else {
		questionMode.value = () => '/api/year'
	}
}

// Fetch a new question and populate the UI state.
const fetchQuestion = async (sourceLabel) => {
  try {
	const apiUrl = questionMode.value()
    console.log(`fetching question (${sourceLabel}):`, apiUrl)

    const response = await axios.get(apiUrl)
    const responseData = response.data
	// if apiUrl is /api/year, we need to generate the year options
	if (apiUrl === '/api/year') {
		const currentYear = new Date().getFullYear()
    	const minYear = responseData.year - 4
    	const maxYear = responseData.year + 4
    	const candidates = Array.from({ length: maxYear - minYear + 1 }, (_, i) => minYear + i)
      		.filter((year) => year !== responseData.year && year < currentYear)
	  		.sort(() => Math.random() - 0.5).slice(0, 3)

    	questions.value.name = responseData.name
		questions.value.mode = 'year'
    	questions.value.answer = responseData.year
		questions.value.options = [responseData.year, ...candidates].sort(() => Math.random() - 0.5)
	}

	// If apiUrl is /api/city, we need to generate city options among the cities list
	if (apiUrl === '/api/city') {
		questions.value.name = responseData.name
		questions.value.mode = 'city'
		questions.value.answer = responseData.city
		const candidates = cities.value
			.filter((city) => city && city !== responseData.city)
			.sort(() => Math.random() - 0.5)
			.slice(0, 3)
		questions.value.options = [responseData.city, ...candidates].sort(() => Math.random() - 0.5)
	}
    console.log(`questions updated (${sourceLabel}):`, { ...questions.value })
  } catch (error) {
    console.error(error)
  }
}

// Initialize data once the component is mounted.
onMounted(async () => {
  await initDatasetInfo()
  if (hasPhotos.value) {
    await fetchQuestion('onMounted')
  }
})

// Reset selection and load a new question.
const newQuestion = async () => {
  selected.value = null
  if (!hasPhotos.value) return
  await fetchQuestion('newQuestion')
}

// Handle selecting an answer option.
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
				<!-- If the question is about year, show "¿De que año es esta foto?" -->
				<span v-if="questions.mode === 'year'" class="question">¿De que año es esta foto?</span>
				<!-- If the question is about city, show "¿De que ciudad es esta foto?" -->
				<span v-else class="question">¿De que ciudad es esta foto?</span>
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
