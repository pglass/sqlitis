import React from 'react';
import ReactDOM from 'react-dom';
import $ from 'jquery';

class SQLForm extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      value: '',
      output: '',
    };

    this.handleChange = this.handleChange.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
  }

  handleChange(event) {
    this.setState({value: event.target.value});
  }

  handleSubmit(event) {
    var successFn = function(data) {
      console.log("Got data", data);
      this.setState({output: data.sqla});
    }

    $.ajax({
      type: "POST",
      url: "/to-sqla",
      dataType: 'json',
      data: JSON.stringify(
        {"sql": this.state.value}
      ),
      success: successFn.bind(this),
    });
    event.preventDefault();
  }

  render() {
    return (
      <form onSubmit={this.handleSubmit}>
        <label>
          SQL:
          <input type="text" value={this.state.value} onChange={this.handleChange} />
        </label>
        <input type="submit" value="Submit" />
        <br/>
        SQL Alchemy: <pre>{this.state.output}</pre>
      </form>
    )
  }
}


ReactDOM.render(<SQLForm />, document.getElementById("main"));
