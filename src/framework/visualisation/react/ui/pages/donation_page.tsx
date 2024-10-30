import { Weak } from '../../../../helpers'
import TextBundle from '../../../../text_bundle'
import { Translator } from '../../../../translator'
import { Translatable } from '../../../../types/elements'
import { PropsUIPageDonation } from '../../../../types/pages'
import { 
    isPropsUIPromptProgress,
    isPropsUIPromptConfirm, 
    isPropsUIPromptConsentForm,
    isPropsUIPromptFileInput,
    isPropsUIPromptFileInputMultiple,
    isPropsUIPromptRadioInput,
    isPropsUIPromptQuestionnaire 
} from '../../../../types/prompts'
import { ReactFactoryContext } from '../../factory'
import { ForwardButton } from '../elements/button'
import { Title1 } from '../elements/text'
import { Confirm } from '../prompts/confirm'
import { ConsentForm } from '../prompts/consent_form'
import { FileInput } from '../prompts/file_input'
import { FileInputMultiple } from '../prompts/file_input_multiple'
import { Progress } from '../prompts/progress'
import { Questionnaire } from '../prompts/questionnaire'
import { RadioInput } from '../prompts/radio_input'
import { Footer } from './templates/footer'
import { Page } from './templates/page'

type Props = Weak<PropsUIPageDonation> & ReactFactoryContext

export const DonationPage = (props: Props): JSX.Element => {
  const { title, forwardButton } = prepareCopy(props)
  const { locale, resolve } = props

  function renderBody (props: Props): JSX.Element {
    const context = { locale: locale, resolve: props.resolve }
    const body = props.body
    if (isPropsUIPromptFileInput(body)) {
      return <FileInput {...body} {...context} />
    }
    if (isPropsUIPromptFileInputMultiple(body)) {
      return <FileInputMultiple {...body} {...context} />
    }
    if (isPropsUIPromptProgress(body)) {
      return <Progress {...body} {...context} />
    }
    if (isPropsUIPromptConfirm(body)) {
      return <Confirm {...body} {...context} />
    }
    if (isPropsUIPromptConsentForm(body)) {
      return <ConsentForm {...body} {...context} />
    }
    if (isPropsUIPromptRadioInput(body)) {
      return <RadioInput {...body} {...context} />
    }
    if (isPropsUIPromptQuestionnaire(body)) {
      return <Questionnaire {...body} {...context} />
    }
    throw new TypeError('Unknown body type')
  }

  function handleSkip (): void {
    resolve?.({ __type__: 'PayloadFalse', value: false })
  }

  function renderFooter (props: Props): JSX.Element | undefined {
    if (props.footer != null) {
      return <Footer
      right={
        <div className='flex flex-row'>
          <div className='flex-grow' />
          <ForwardButton label={forwardButton} onClick={handleSkip} />
        </div>
      } />
    } else {
      return undefined
    }
  }

  const footer: JSX.Element = (
    <>
      {renderFooter(props)}
    </>
  )


  const body: JSX.Element = (
    <>
      <Title1 text={title} />
      {renderBody(props)}
    </>
  )

  return (
    <Page body={body} footer={footer}/>
  )
}

interface Copy {
  title: string
  forwardButton: string
}

function prepareCopy ({ header: { title }, locale }: Props): Copy {
  return {
    title: Translator.translate(title, locale),
    forwardButton: Translator.translate(forwardButtonLabel(), locale)
  }
}

const forwardButtonLabel = (): Translatable => {
  return new TextBundle()
    .add('en', 'Skip')
    .add('de', 'Überspringen')
    .add('nl', 'Overslaan')
}