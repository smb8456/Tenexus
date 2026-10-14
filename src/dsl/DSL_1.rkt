#lang racket

;; KeyRules: a small DSL for routing tenant maintenance requests.
;; Emergency requests take priority over ordinary maintenance requests.

(provide define-keyrules route-request)

(struct emergency-rule (keywords action) #:transparent)
(struct vendor-rule (keywords vendor) #:transparent)
(struct keyrules (emergency-rules vendor-rules) #:transparent)

(define (normalize s)
  (string-downcase (string-trim s)))

(define (contains-any? text keywords)
  (for/or ([k keywords])
    (regexp-match? (regexp (regexp-quote (normalize k))) text)))

(define (define-keyrules . rules)
  (define emergency-rules '())
  (define vendor-rules '())
  (for ([r rules])
    (match r
      [(list 'emergency keywords action)
       (set! emergency-rules (cons (emergency-rule keywords action) emergency-rules))]
      [(list 'vendor keywords vendor)
       (set! vendor-rules (cons (vendor-rule keywords vendor) vendor-rules))]
      [_ (error 'define-keyrules "invalid rule: ~a" r)]))
  (keyrules (reverse emergency-rules) (reverse vendor-rules)))

(define (route-request rules request)
  (define text (normalize request))
  (cond
    [(for/or ([r (keyrules-emergency-rules rules)])
       (and (contains-any? text (emergency-rule-keywords r))
            (emergency-rule-action r)))
     => values]
    [(for/or ([r (keyrules-vendor-rules rules)])
       (and (contains-any? text (vendor-rule-keywords r))
            (vendor-rule-vendor r)))
     => (lambda (vendor) (format "Send to vendor: ~a" vendor))]
    [else "Escalate to landlord for human review"]))

(module+ examples
  (define rules
    (define-keyrules
      '(emergency ("gas smell" "gas leak") "Escalate to landlord immediately")
      '(emergency ("fire" "smoke") "Escalate to landlord immediately")
      '(vendor ("leaking sink" "sink leak" "leak in sink") "plumbing vendor")))

  (displayln (route-request rules "There is a gas smell in the kitchen."))
  (displayln (route-request rules "The sink is leaking under the cabinet."))
  (displayln (route-request rules "My heater is making noise.")))

(module+ test
  (require rackunit)

  (define rules
    (define-keyrules
      '(emergency ("gas smell" "gas leak") "Escalate to landlord immediately")
      '(emergency ("fire" "smoke") "Escalate to landlord immediately")
      '(vendor ("leaking sink" "sink leak" "leak in sink") "plumbing vendor")))

  (check-equal? (route-request rules "Gas smell in the apartment")
                "Escalate to landlord immediately")
  (check-equal? (route-request rules "There is a fire in the building")
                "Escalate to landlord immediately")
  (check-equal? (route-request rules "Leaking sink in the kitchen")
                "Send to vendor: plumbing vendor")
  (check-equal? (route-request rules "Trash question")
                "Escalate to landlord for human review"))

(module+ main
  (require (submod ".." examples)))
