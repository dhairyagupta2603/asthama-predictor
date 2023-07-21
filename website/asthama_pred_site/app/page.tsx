import Image from 'next/image'

import Header from './_header'

export default function Home() {
  return (
    <>
    <Header
      aboutLink={{url: '#'}}
      consentLink={{url: '#'}}
      websiteName='Phonon Asthma Predictor'
    />
    </>
  )
}
