#lang racket
(require rackunit "triage.rkt")

(define nine
  '(("I smell gas in the kitchen" . escalate)
    ("I am locked out of my apartment" . escalate)
    ("There is smoke coming from the outlet" . escalate)
    ("Water is coming through the ceiling" . escalate)
    ("My sink is leaking" . vendor)
    ("The toilet is clogged" . vendor)
    ("The light switch in the hall is broken" . vendor)
    ("When is trash day?" . answer)
    ("What are the quiet hours?" . answer)))

;; Each of the nine requests routes as expected (9 checks)
(for ([pair nine])
  (check-equal? (decision-route (triage default-rules (car pair))) (cdr pair) (car pair)))

;; Safety rule wins over the electrician rule
(check-equal? (decision-urgency (triage default-rules "smoke from the outlet")) 10)

;; Vendor name comes from the rule data
(check-equal? (decision-detail (triage default-rules "My sink is leaking")) "Liberty Plumbing")

;; Purity: same input twice gives equal results
(check-equal? (triage default-rules "My sink is leaking") (triage default-rules "My sink is leaking"))

;; Immutability: the rule list is unchanged after triaging
(let ([before default-rules])
  (triage-all default-rules (map car nine))
  (check-equal? default-rules before))

;; foldl counts: 4 escalate, 3 vendor, 2 answer
(check-equal? (count-routes (triage-all default-rules (map car nine)))
              (hash 'escalate 4 'vendor 3 'answer 2))

;; An empty rule list escalates everything
(check-equal? (decision-route (triage '() "anything")) 'escalate)
