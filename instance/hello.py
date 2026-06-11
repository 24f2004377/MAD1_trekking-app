import turtle 
pen=turtle.Turtle()
pen.color("red")
pen.speed(3)
for i in range(6):
    pen.circle(100,60)
    pen.left(120)
    pen.circle(100,60)
    pen.left(120)
    pen.left(60)
pen.hideturtle()
turtle.done()