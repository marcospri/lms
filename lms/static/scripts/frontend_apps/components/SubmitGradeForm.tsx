import {
  Button,
  CancelIcon,
  CheckIcon,
  IconButton,
  Input,
  Spinner,
  SpinnerOverlay,
  NoteIcon,
  NoteFilledIcon,
  PointerUpIcon,
  Textarea,
} from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import {
  useEffect,
  useLayoutEffect,
  useState,
  useRef,
  useCallback,
  useMemo,
  useId,
} from 'preact/hooks';

import type { StudentInfo } from '../config';
import type { ErrorLike } from '../errors';
import { useService, GradingService } from '../services';
import { useFetch } from '../utils/fetch';
import { formatGrade, validateGrade } from '../utils/grade-validation';
import { useUniqueId } from '../utils/hooks';
import { useWarnOnPageUnload } from '../utils/use-warn-on-page-unload';
import ErrorModal from './ErrorModal';
import ValidationMessage from './ValidationMessage';

export type SubmitGradeFormProps = {
  student: StudentInfo | null;

  /**
   * Scaling factor applied to grade values from the LMS to get the values
   * entered by the user. Default value is 10.
   *
   * LTI 1.1 only supports grade values between 0 and 1, which we then rescale
   * to 0-{scoreMaximum} in the UI. LTI 1.3+ offer more flexibility (see [1]).
   *
   * [1] https://www.imsglobal.org/spec/lti-ags/v2p0
   */
  scoreMaximum?: number;

  /** It lets parent components know if there are unsaved changes in the grading form */
  onUnsavedChanges?: (hasUnsavedChanges: boolean) => void;

  /**
   * Allow instructors to provide an extra comment together with the grade value.
   * Default value is false.
   */
  acceptGradingComments?: boolean;
};

const DEFAULT_MAX_SCORE = 10;

/**
 * A form with a single input field and submit button for an instructor to
 * save a student's grade.
 */
export default function SubmitGradeForm({
  student,
  onUnsavedChanges,
  scoreMaximum = DEFAULT_MAX_SCORE,
  acceptGradingComments = false,
}: SubmitGradeFormProps) {
  const [fetchGradeErrorDismissed, setFetchGradeErrorDismissed] =
    useState(false);
  const gradingService = useService(GradingService);

  const fetchGrade = async (student: StudentInfo) => {
    setFetchGradeErrorDismissed(false);
    const { currentScore = null, comment } = await gradingService.fetchGrade({
      student,
    });
    return {
      grade: formatGrade(currentScore, scoreMaximum),
      comment,
    };
  };

  // The stored grade value fetched from the LMS and converted to the range
  // displayed in the UI.
  const grade = useFetch(
    student ? `grade:${student.userid}` : null,
    student ? () => fetchGrade(student) : undefined
  );

  // The following is state for saving the grade
  //
  // If there is an error when submitting a grade?
  const [submitGradeError, setSubmitGradeError] = useState<ErrorLike | null>(
    null
  );
  // Is set to true when the grade is being currently posted to the service
  const [gradeSaving, setGradeSaving] = useState(false);
  // Changes the input field's background to green for a short duration when true
  const [gradeSaved, setGradeSaved] = useState(false);

  const disabled = !student;

  // Comment-related state
  const [showCommentControls, setShowCommentControls] = useState(false);
  const [draftCommentValue, setDraftCommentValue] = useState<string | null>(
    null
  );
  const commentIsSet =
    !disabled && (!!draftCommentValue || !!grade.data?.comment);
  const commentId = useId();
  const commentRef = useRef<HTMLTextAreaElement | null>(null);

  // The following is state for local validation errors
  //
  // Is there a validation error message to show?
  const [showValidationError, setValidationError] = useState(false);
  // The actual validation error message.
  const [validationMessage, setValidationMessageMessage] = useState('');
  // Unique id attribute for <input>
  const gradeId = useUniqueId('SubmitGradeForm__grade:');

  // Used to handle keyboard input changes for the grade input field.
  const inputRef = useRef<HTMLInputElement | null>(null);

  // This is used to track an unsaved grade. It is null until user input occurs.
  const [draftGradeValue, setDraftGradeValue] = useState<string | null>(null);

  // Track if current grade has changed compared to what was originally loaded
  const hasUnsavedChanges = useMemo(
    () =>
      (draftGradeValue !== null && draftGradeValue !== grade.data?.grade) ||
      (draftCommentValue !== null && draftCommentValue !== grade.data?.comment),
    [draftCommentValue, draftGradeValue, grade.data?.comment, grade.data?.grade]
  );

  // Make sure instructors are notified if there's a risk to lose unsaved data
  useWarnOnPageUnload(hasUnsavedChanges);

  // Clear the previous grade and hide comment controls when the user changes.
  useEffect(() => {
    setGradeSaved(false);
    setShowCommentControls(false);
    setDraftGradeValue(null);
    setDraftCommentValue(null);
  }, [student]);

  useLayoutEffect(() => {
    inputRef.current!.focus();
    inputRef.current!.select();
  }, [grade]);

  const onSubmitGrade = async (event: Event) => {
    event.preventDefault();

    const newGrade = inputRef.current!.value;
    const newComment = acceptGradingComments
      ? commentRef.current!.value
      : undefined;
    const result = validateGrade(newGrade, scoreMaximum);

    if (!result.valid) {
      setValidationMessageMessage(result.error);
      setValidationError(true);
    } else {
      setGradeSaving(true);
      try {
        await gradingService.submitGrade({
          student: student as StudentInfo,
          grade: result.grade,
          comment: newComment,
        });
        grade.mutate({ grade: newGrade, comment: newComment });
        onUnsavedChanges?.(false);
        setShowCommentControls(false);
        setGradeSaved(true);
      } catch (e) {
        setSubmitGradeError(e);
      }
      setGradeSaving(false);
    }
  };

  const handleInputCommon = useCallback((e: Event): string => {
    // If any input is detected, close the ValidationMessage.
    setValidationError(false);
    setGradeSaved(false);

    return (e.target as HTMLInputElement).value;
  }, []);
  const handleGradeInput = useCallback(
    (e: Event) => {
      const newGrade = handleInputCommon(e);
      setDraftGradeValue(newGrade);

      // Check if there are unsavedChanges
      onUnsavedChanges?.(
        newGrade !== grade.data?.grade ||
          (draftCommentValue !== null &&
            draftCommentValue !== grade.data.comment)
      );
    },
    [
      handleInputCommon,
      onUnsavedChanges,
      grade.data?.grade,
      grade.data?.comment,
      draftCommentValue,
    ]
  );
  const handleCommentInput = useCallback(
    (e: Event) => {
      const newComment = handleInputCommon(e);
      setDraftCommentValue(newComment);

      // Check if there are unsavedChanges
      onUnsavedChanges?.(
        newComment !== grade.data?.comment ||
          (draftGradeValue !== null && draftGradeValue !== grade.data.grade)
      );
    },
    [
      handleInputCommon,
      onUnsavedChanges,
      grade.data?.comment,
      grade.data?.grade,
      draftGradeValue,
    ]
  );

  return (
    <>
      <form autoComplete="off">
        <label htmlFor={gradeId} className="font-semibold text-xs">
          Grade (Out of {scoreMaximum})
        </label>
        <div className="flex">
          <span className="relative w-14">
            {validationMessage && (
              <ValidationMessage
                message={validationMessage}
                open={showValidationError}
                onClose={() => {
                  // Sync up the state when the ValidationMessage is closed
                  setValidationError(false);
                }}
              />
            )}
            <Input
              classes={classnames(
                'text-center',
                'disabled:opacity-50',
                'border border-r-0 rounded-r-none',
                {
                  'animate-gradeSubmitSuccess': gradeSaved,
                }
              )}
              data-testid="grade-input"
              disabled={disabled}
              id={gradeId}
              elementRef={inputRef}
              onInput={handleGradeInput}
              type="text"
              value={draftGradeValue ?? grade.data?.grade ?? ''}
              key={student ? student.LISResultSourcedId : null}
            />
            {grade.isLoading && (
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                <Spinner size="md" />
              </div>
            )}
          </span>

          {acceptGradingComments && (
            <span className="relative">
              <Button
                icon={commentIsSet ? NoteFilledIcon : NoteIcon}
                disabled={disabled}
                title={commentIsSet ? 'Edit comment' : 'Add comment'}
                onClick={() => setShowCommentControls(prev => !prev)}
                classes={classnames(
                  'border border-r-0 rounded-none ring-inset h-full relative',
                  'disabled:opacity-50'
                )}
              />
              {showCommentControls && (
                <div
                  className={classnames(
                    'w-80 p-3',
                    'shadow border rounded bg-white',
                    'absolute top-[calc(100%+3px)] right-0'
                  )}
                >
                  <PointerUpIcon
                    className={classnames(
                      'text-grey-3 fill-white',
                      'absolute inline z-2 w-[15px]',
                      // Position arrow over "Add comment" button
                      'right-[7px] top-[-9px]'
                    )}
                  />
                  <div className="flex items-center">
                    <label htmlFor={commentId} className="font-bold">
                      Add a comment:
                    </label>
                    <div className="grow" />
                    <IconButton
                      title="Close comment"
                      icon={CancelIcon}
                      classes="hover:bg-grey-3/50"
                      onClick={() => setShowCommentControls(false)}
                    />
                  </div>
                  <Textarea
                    id={commentId}
                    classes="mt-1"
                    rows={10}
                    elementRef={commentRef}
                    value={draftCommentValue ?? grade.data?.comment ?? ''}
                    onInput={handleCommentInput}
                  />
                  <div className="flex flex-row-reverse space-x-2 space-x-reverse mt-3">
                    <Button
                      variant="primary"
                      disabled={disabled}
                      onClick={onSubmitGrade}
                    >
                      Submit Grade
                    </Button>
                    <Button
                      icon={CancelIcon}
                      onClick={() => setShowCommentControls(false)}
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              )}
            </span>
          )}

          <Button
            icon={CheckIcon}
            type="submit"
            classes={classnames(
              'border rounded-l-none ring-inset',
              'disabled:opacity-50'
            )}
            disabled={disabled}
            onClick={onSubmitGrade}
          >
            Submit Grade
          </Button>
        </div>
        {gradeSaving && <SpinnerOverlay />}
      </form>
      {!!submitGradeError && (
        <ErrorModal
          description="Unable to submit grade"
          error={submitGradeError}
          onCancel={() => {
            setSubmitGradeError(null);
          }}
          cancelLabel="Close"
        />
      )}
      {grade.error && !fetchGradeErrorDismissed && (
        <ErrorModal
          description="Unable to fetch grade"
          error={grade.error}
          cancelLabel="Close"
          onCancel={() => setFetchGradeErrorDismissed(true)}
        />
      )}
    </>
  );
}
