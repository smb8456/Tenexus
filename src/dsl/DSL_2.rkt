#lang racket

;; DSL_2.rkt
;; KeyFAQ: a simple FAQ DSL for approved tenant answers.
;;
;; This file defines a small domain-specific language that lets landlords
;; register property-specific approved answers for common tenant questions.
;; Unknown questions are escalated for human review.

(provide define-keyfaq
         match-question
         faq-answer
         faq-rules
         faq-entry?)

(struct faq-entry (keywords answer) #:transparent)

(define (normalize-text s)
  (string-downcase (string-trim s)))

(define (contains-keyword? question keyword)
  (regexp-match? (regexp (regexp-quote (normalize-text keyword)))
                (normalize-text question)))

(define (entry-matches? entry question)
  (ormap (lambda (kw) (contains-keyword? question kw))
         (faq-entry-keywords entry)))

(define (faq-answer-entry entry)
  (faq-entry-answer entry))

(define (faq-answer rules question)
  (define matched
    (for/first ([entry (in-list rules)]
                #:when (entry-matches? entry question))
      entry))
  (if matched
      (faq-answer-entry matched)
      "Escalate to human review."))

(define-syntax-rule (define-keyfaq rule ...)
  (list rule ...))

(define-syntax-rule (match-question rules question)
  (faq-answer rules question))

;; -----------------------------------------------------------------------------
;; Example KeyFAQ definitions
;; -----------------------------------------------------------------------------

(define example-faq
  (define-keyfaq
    (faq-entry '("trash day" "when is trash collection" "trash collection")
               "Trash is collected every Tuesday morning. Please place bins at the curb the night before.")
    (faq-entry '("parking" "where can i park" "guest parking")
               "Resident parking is assigned by unit. Guest parking is available in the marked visitor spaces.")
    (faq-entry '("where do i place trash" "trash pickup")
               "Please place trash bins in the designated collection area near the side gate.")))

(module+ examples
  (displayln (match-question example-faq "When is trash collection?"))
  (displayln (match-question example-faq "Where can I park?"))
  (displayln (match-question example-faq "How do I reset the thermostat?")))

(module+ test
  (require rackunit)

  (test-case "trash collection question matches approved answer"
    (check-equal?
     (match-question example-faq "When is trash collection?")
     "Trash is collected every Tuesday morning. Please place bins at the curb the night before."))

  (test-case "parking question matches approved answer"
    (check-equal?
     (match-question example-faq "Where can I park?")
     "Resident parking is assigned by unit. Guest parking is available in the marked visitor spaces."))

  (test-case "unknown question escalates for human review"
    (check-equal?
     (match-question example-faq "How do I reset the thermostat?")
     "Escalate to human review."))

  (test-case "property-specific alternate trash wording matches"
    (check-equal?
     (match-question example-faq "Where do I place trash?")
     "Please place trash bins in the designated collection area near the side gate.")))
