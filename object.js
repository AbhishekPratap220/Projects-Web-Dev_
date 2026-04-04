// Creating a javascript object 
let person ={
    firstName : "Abhishek ",
    lastName : "Thakur",
    age : 23,
    occupation : "student",

    // Method 
    fullName : function(){
        return this.firstName + " " + this .lastName;
    },

    //Another method
    introduce : function(){
        return `Hello , my name is ${this.fullName()} and I am a ${this.occupation}.`;
    }
};

// Using the object 
console.log(person.fullName());
console.log(person.introduce());